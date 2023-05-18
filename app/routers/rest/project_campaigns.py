# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import datetime
import logging
from typing import (Any, List)

from fastapi import (APIRouter,
                     HTTPException,
                     Response,
                     Security)
from starlette.background import BackgroundTasks
from starlette.requests import Request

from app.app_exception import (CampaignNotFound,
                               DuplicateTestResults,
                               IncorrectFieldsRequest,
                               MalformedCsvFile,
                               VersionNotFound)
from app.database.authorization import authorize_user
from app.database.postgre.pg_campaigns_management import (
    create_campaign,
    retrieve_campaign,
    update_campaign_occurrence as pg_update_campaign_occurrence)
from app.database.postgre.pg_test_results import insert_result as pg_insert_result
from app.database.postgre.testcampaign import (db_get_campaign_ticket_scenario,
                                               db_get_campaign_ticket_scenarios,
                                               db_get_campaign_tickets,
                                               db_put_campaign_ticket_scenarios,
                                               db_set_campaign_ticket_scenario_status,
                                               fill_campaign as db_fill_campaign,
                                               get_campaign_content)
from app.database.redis.rs_file_management import rs_record_file, rs_retrieve_file
from app.database.utils.object_existence import if_error_raise_http, project_version_raise
from app.database.utils.test_result_management import register_manual_campaign_result
from app.schema.campaign_schema import (CampaignFull,
                                        CampaignLight,
                                        CampaignPatch,
                                        Scenarios,
                                        TicketScenarioCampaign,
                                        ToBeCampaign)
from app.schema.postgres_enums import (CampaignStatusEnum,
                                       ScenarioStatusEnum)
from app.schema.project_schema import (ErrorMessage)
from app.schema.rest_enum import DeliverableTypeEnum
from app.utils.log_management import log_error
from app.utils.report_generator import campaign_deliverable

router = APIRouter(
    prefix="/api/v1/projects"
)

log = logging.getLogger(__name__)


# Create blank campaign for version
@router.post("/{project_name}/campaigns",
             tags=["Campaign"],
             description="Create a new campaign linked to a project-version."
                         " Multiple occurrence of the same campaign can be created",
             response_model=CampaignLight,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case),"
                                      " the version does not exist"},
                 401: {"model": ErrorMessage,
                       "description": "You are not authenticated"},
                 422: {"model": ErrorMessage,
                       "description": "Payload does not match the expected schema"},
                 500: {"model": ErrorMessage,
                       "description": "The server could not compute the result."}
             }
             )
async def create_campaigns(project_name: str,
                           campaign: ToBeCampaign,
                           user: Any = Security(authorize_user, scopes=["admin"])):
    await project_version_raise(project_name, campaign.version)
    try:
        return await create_campaign(project_name, campaign.version)
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp


# Link tickets & scenarios to campaign
# { "tickets": [{"epic", "feature", "scenario_id"}...]}
@router.put("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Campaign"],
            description="Fill the campaign with ticket and scenarios",
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case),"
                                     " the version does not exist,"
                                     " the campaign-occurrence does not exist"},
                401: {"model": ErrorMessage,
                      "description": "You are not authenticated"}
            }
            )
async def fill_campaign(project_name: str,
                        version: str,
                        occurrence: str,
                        content: TicketScenarioCampaign,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    await project_version_raise(project_name, version)
    try:
        campaign_ticket_id, errors = await db_fill_campaign(project_name,
                                                            version,
                                                            occurrence,
                                                            content)
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp

    return {"campaign_ticket_id": if_error_raise_http(campaign_ticket_id),
            "errors": errors}


@router.get("/{project_name}/campaigns",
            tags=["Campaign"],
            description="Retrieve campaign")
async def get_campaigns(project_name: str,
                        response: Response,
                        version: str = None,
                        status: CampaignStatusEnum = None,
                        limit: int = 10,
                        skip: int = 0):
    await project_version_raise(project_name, version)
    try:
        campaigns, count = await retrieve_campaign(project_name,
                                                   version,
                                                   status,
                                                   limit=limit,
                                                   skip=skip)
        response.headers["X-total-count"] = str(
            count)  # TODO check reason it doesn't work wthout cast
        return campaigns
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp


@router.patch("/{project_name}/campaigns/{version}/{occurrence}",
              tags=["Campaign"],
              response_model=CampaignLight,
              description="Update the status of an occurrence",
              responses={
                  400: {"model": ErrorMessage,
                        "description": "version already exist"},
                  401: {"model": ErrorMessage,
                        "description": "You are not authenticated"},
                  404: {"model": ErrorMessage,
                        "description": "Project name is not registered (ignore case),"
                                       " the version does not exist,"
                                       " the campaign-occurrence does not exist"},
                  422: {"model": ErrorMessage,
                        "description": "The payload does not match the expected schema"}

              })
async def update_campaign_occurrence(project_name: str,
                                     version: str,
                                     occurrence: str,
                                     campaign_update: CampaignPatch,
                                     user: Any = Security(authorize_user, scopes=["admin"])):
    await project_version_raise(project_name, version)
    try:
        res = await pg_update_campaign_occurrence(project_name,
                                                  version,
                                                  occurrence,
                                                  campaign_update)
        if res.statusmessage != 'UPDATE 1':
            raise Exception(f"Request has not been computed.\nGet '{res.statusmessage}'")
        res = await get_campaign_content(project_name, version, occurrence, True)
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(res)


# Retrieve campaign for project


# Retrieve campaign for project-version
@router.get("/{project_name}/campaigns/{version}/{occurrence}",
            response_model=CampaignFull,
            tags=["Campaign"],
            description="Retrieve the full campaign",
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case),"
                                     " the version does not exist,"
                                     " the campaign-occurrence does not exist"},
                500: {"model": ErrorMessage,
                      "description": "The server could not compute the result."}
            }
            )
async def get_campaign(project_name: str,
                       version: str,
                       occurrence: str):
    await project_version_raise(project_name, version)
    try:
        result = await get_campaign_content(project_name, version, occurrence)
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)


# Retrieve scenarios for project-version-campaign-ticket
@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets",
            tags=["Campaign"],
            description="Retrieve a campaign tickets")
async def get_campaign_tickets(project_name: str,
                               version: str,
                               occurrence: str):
    await project_version_raise(project_name, version)
    try:
        return await db_get_campaign_tickets(project_name, version, occurrence)
    except CampaignNotFound as cnf:
        raise HTTPException(404, detail=" ".join(cnf.args)) from cnf
    except Exception as exp:
        raise HTTPException(500, repr(exp)) from exp


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_ref}",
            tags=["Campaign"],
            description="Retrieve a campaign ticket")
async def get_campaign_ticket(project_name: str,
                              version: str,
                              occurrence: str,
                              ticket_ref: str):
    try:
        return await db_get_campaign_ticket_scenarios(project_name, version, occurrence, ticket_ref)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.put("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_ref}",
            tags=["Campaign"],
            description="Add scenarios to a ticket")
async def put_campaign_ticket_scenarios(project_name: str,
                                        version: str,
                                        occurrence: str,
                                        ticket_ref: str,
                                        scenarios: List[Scenarios],
                                        user: Any = Security(authorize_user,
                                                             scopes=["admin", "user"])
                                        ):
    try:
        return await db_put_campaign_ticket_scenarios(project_name,
                                                      version,
                                                      occurrence,
                                                      ticket_ref,
                                                      scenarios)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


# Retrieve scenario_internal_id for specific campaign and ticket
@router.get("/{project_name}/campaigns/{version}/{occurrence}/"
            "tickets/{reference}/scenarios/{scenario_id}",
            tags=["Campaign"])
async def get_campaign_ticket_scenario(project_name: str,
                                       version: str,
                                       occurrence: str,
                                       reference: str,
                                       scenario_id: str):
    try:
        return await db_get_campaign_ticket_scenario(project_name,
                                                     version,
                                                     occurrence,
                                                     reference,
                                                     scenario_id)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.put("/{project_name}/campaigns/{version}/{occurrence}/"
            "tickets/{reference}/scenarios/{scenario_id}/status",
            tags=["Campaign"])
async def update_campaign_ticket_scenario_status(project_name: str,
                                                 version: str,
                                                 occurrence: str,
                                                 reference: str,
                                                 scenario_id: str,
                                                 new_status: ScenarioStatusEnum,
                                                 user: Any = Security(authorize_user,
                                                                      scopes=["admin", "user"])):
    try:
        return await db_set_campaign_ticket_scenario_status(project_name,
                                                            version,
                                                            occurrence,
                                                            reference,
                                                            scenario_id,
                                                            new_status)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.post("/{project_name}/campaigns/{version}/{occurrence}/",
             tags=["Campaign"])
async def create_campaign_occurrence_result(project_name: str,
                                            version: str,
                                            occurrence: str,
                                            background_task: BackgroundTasks,
                                            user: Any = Security(authorize_user,
                                                                 scopes=["admin", "user"])):
    try:
        test_result_uuid, campaign_id, scenarios = await register_manual_campaign_result(
            project_name,
            version,
            occurrence)
        background_task.add_task(pg_insert_result,
                                 datetime.datetime.now(),
                                 project_name,
                                 version,
                                 campaign_id,
                                 True,
                                 test_result_uuid,
                                 scenarios)
        return test_result_uuid
    except IncorrectFieldsRequest as ifr:
        raise HTTPException(400, detail="".join(ifr.args)) from ifr
    except DuplicateTestResults as dtr:
        raise HTTPException(400, detail=" ".join(dtr.args)) from dtr
    except MalformedCsvFile as mcf:
        raise HTTPException(400, detail=" ".join(mcf.args)) from mcf
    except VersionNotFound as vnf:
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.get("/{project_name}/campaigns/{version}/{occurrence}/deliverables",
            tags=["Campaign-Deliverables"])
async def retrieve_campaign_occurrence_deliverables(project_name: str,
                                                    version: str,
                                                    occurrence: str,
                                                    request: Request,
                                                    deliverable_type: DeliverableTypeEnum =
                                                    DeliverableTypeEnum.TEST_PLAN,
                                                    ticket_ref: str = None,
                                                    user: Any = Security(authorize_user,
                                                                         scopes=["admin", "user"])
                                                    ):
    try:
        if ticket_ref is not None:
            key = f"file:{project_name}:{version}:{occurrence}:{ticket_ref}:" \
                  f"{deliverable_type.value}"
        else:
            key = f"file:{project_name}:{version}:{occurrence}:{deliverable_type.value}"
        filename = await rs_retrieve_file(key)
        if filename is None:
            filename = await campaign_deliverable(project_name,
                                                  version,
                                                  occurrence,
                                                  deliverable_type,
                                                  ticket_ref)
            await rs_record_file(key, filename)
        return f"{request.base_url}static/{filename}"
    except VersionNotFound as vnf:
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf
    except Exception as exp:
        raise HTTPException(500, repr(exp)) from exp
