# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import datetime
import json

from fastapi import APIRouter, Form
from starlette.background import BackgroundTasks
from starlette.requests import Request

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import is_updatable
from app.database.postgre.pg_campaigns_management import create_campaign, retrieve_campaign, update_campaign_occurrence
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_test_results import TestResults
from app.database.postgre.pg_test_results import insert_result as pg_insert_result
from app.database.postgre.pg_tickets_management import get_tickets_not_in_campaign
from app.database.postgre.pg_versions import get_versions
from app.database.postgre.testcampaign import (
    db_delete_campaign_ticket_scenario,
    db_get_campaign_ticket_scenario,
    db_get_campaign_ticket_scenarios,
    db_get_campaign_tickets,
    db_put_campaign_ticket_scenarios,
    db_set_campaign_ticket_scenario_status,
    get_campaign_content,
)
from app.database.postgre.testrepository import db_project_epics, db_project_features, db_project_scenarios
from app.database.redis.rs_file_management import rs_invalidate_file, rs_record_file, rs_retrieve_file
from app.database.utils.output_strategy import REGISTERED_OUTPUT
from app.database.utils.test_result_management import register_manual_campaign_result
from app.database.utils.ticket_management import add_tickets_to_campaign
from app.database.utils.what_strategy import REGISTERED_STRATEGY
from app.schema.campaign_schema import CampaignPatch, Scenarios
from app.schema.error_code import ApplicationError
from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum
from app.schema.rest_enum import (
    DeliverableTypeEnum,
    RestTestResultCategoryEnum,
    RestTestResultHeaderEnum,
    RestTestResultRenderingEnum,
)
from app.utils.log_management import log_error, log_message
from app.utils.pages import page_numbering
from app.utils.project_alias import provide
from app.utils.report_generator import campaign_deliverable

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/campaigns",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_management(project_name: str,
                                   request: Request,
                                   limit: int = 10,
                                   skip: int = 0
                                   ):
    try:
        if not is_updatable(request, tuple()):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        # campaigns,  = retrieve_campaign(project_name)

        if request.headers.get("eaid-request", "") == "table":
            return await front_project_table(project_name,
                                             request,
                                             limit,
                                             skip)
        if request.headers.get("eaid-request", "") == "form":
            return await front_new_campaign_form(project_name,
                                                 request)
        if request.headers.get("eaid-request", "") == "REDIRECT":
            return templates.TemplateResponse("void.html",
                                              {
                                                  "request": request
                                              },
                                              headers={
                                                  "HX-Redirect": f"/front/v1/projects/"
                                                                 f"{project_name}/campaigns"})
        projects = await registered_projects()
        return templates.TemplateResponse("campaign.html",
                                          {
                                              "request": request,
                                              "projects": projects,
                                              "campaigns": True,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def front_project_table(project_name: str,
                              request: Request,
                              limit: int = 10,
                              skip: int = 0):
    try:
        campaigns, count = await retrieve_campaign(project_name, limit=limit, skip=skip)
        pages, current_page = page_numbering(count, limit, skip)
        return templates.TemplateResponse("tables/campaign_table.html",
                                          {
                                              "request": request,
                                              "campaigns": campaigns,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "pages": pages,
                                              "current": current_page,
                                              "nav_bar": count >= limit
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def front_new_campaign_form(project_name: str,
                                  request: Request):
    try:
        return templates.TemplateResponse("forms/add_campaign.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "versions": await get_versions(project_name, True)

                                          },
                                          headers={
                                              "HX-Trigger": request.headers.get("eaid-next", "")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/campaigns",
             tags=["Front - Project"],
             include_in_schema=False
             )
async def front_new_campaign(project_name: str,
                             request: Request,
                             version: str = Form(...)
                             ):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        await create_campaign(project_name, version)
        return templates.TemplateResponse("void.html",
                                          {"request": request},
                                          headers={
                                              "hx-trigger": request.headers.get("eaid-next", "")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/campaigns/scenarios",
             tags=["Front - Campaign"],
             include_in_schema=False)
async def front_scenarios_selector(project_name: str,
                                   body: dict,
                                   request: Request):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        scenarios, count = await db_project_scenarios(project_name, body["epic"], body["feature"])
        return templates.TemplateResponse("forms/add_scenarios_selector.html",
                                          {"project_name": project_name,
                                           "project_name_alias": provide(project_name),
                                           "epic": body["epic"],
                                           "feature": body["feature"],
                                           "scenarios": scenarios,
                                           "request": request})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign(project_name: str,
                             version: str,
                             occurrence: str,
                             request: Request):
    try:
        if not is_updatable(request, tuple()):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox",
                                                       "HX-Reswap": "innerHTML"})
        if request.headers.get("eaid-request", "") == "table":
            campaign = await db_get_campaign_tickets(project_name, version, occurrence)
            return templates.TemplateResponse("tables/campaign_board_table.html",
                                              {"request": request,
                                               "campaign": campaign,
                                               "project_name": project_name,
                                               "version": version,
                                               "occurrence": occurrence})
        if request.headers.get("eaid-request", "") == "form":
            campaign = await get_campaign_content(project_name, version, occurrence, True)
            return templates.TemplateResponse("forms/update_campaign_occurrence.html",
                                              {"request": request,
                                               "campaign": campaign,
                                               "statuses": CampaignStatusEnum.list(),
                                               "project_name": project_name,
                                               "version": version,
                                               "occurrence": occurrence,
                                               "update": False})

        campaign = await get_campaign_content(project_name, version, occurrence, True)
        projects = await registered_projects()
        return templates.TemplateResponse("campaign_board.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "version": version,
                                              "occurrence": occurrence,
                                              "campaign": campaign,
                                              "projects": projects
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.patch("/{project_name}/campaigns/{version}/{occurrence}",
              tags=["Front - Campaign"],
              include_in_schema=False)
async def front_update_campaign(project_name: str,
                                version: str,
                                occurrence: str,
                                body: dict,
                                request: Request):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
            # Do the treatment here
        res = await update_campaign_occurrence(project_name,
                                               version,
                                               occurrence,
                                               CampaignPatch(**body))
        if isinstance(res, ApplicationError):
            raise Exception(f"{res.error}\n{res.message}")
            # Success
        return templates.TemplateResponse("void.html",
                                          {"request": request},
                                          headers={"HX-Trigger": json.dumps({"modalClear": "",
                                                                             "form-delete": ""})})
    except Exception as exception:
        log_error("\n".join(exception.args))
        campaign = await get_campaign_content(project_name, version, occurrence, True)
        return templates.TemplateResponse("forms/update_campaign_occurrence.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "version": version,
                                              "occurrence": occurrence,
                                              "campaign": campaign,
                                              "statuses": CampaignStatusEnum.list(),
                                              "update": True,
                                              "message": "\n".join(exception.args)
                                              # Add the error message
                                          },
                                          headers={"HX-Retarget": "#modal",  # Retarget
                                                   "HX-Reswap": "beforeend"})  # Change swap


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign_ticket_add_scenario(project_name: str,
                                                 version: str,
                                                 occurrence: str,
                                                 ticket_reference: str,
                                                 request: Request,
                                                 initiator: str = None):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        epics = await db_project_epics(project_name)
        if epics:
            features = await db_project_features(project_name, epics[0])
            unique_features = {feature["name"] for feature in features}
        else:
            unique_features = set()
        return templates.TemplateResponse("forms/add_scenarios.html",
                                          {"project_name": project_name,
                                           "project_name_alias": provide(project_name),
                                           "version": version,
                                           "occurrence": occurrence,
                                           "request": request,
                                           "ticket_reference": ticket_reference,
                                           "epics": epics,
                                           "features": unique_features,
                                           "initiator": request.headers.get('eaid-next', '')})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}/scenarios",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign_ticket(project_name: str,
                                    version: str,
                                    occurrence: str,
                                    ticket_reference: str,
                                    request: Request):
    try:
        if not is_updatable(request, tuple()):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        scenarios = await db_get_campaign_ticket_scenarios(project_name,
                                                           version,
                                                           occurrence,
                                                           ticket_reference)
        return templates.TemplateResponse("tables/ticket_scenarios.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "version": version,
                                              "occurrence": occurrence,
                                              "ticket_reference": ticket_reference,
                                              "scenarios": scenarios,
                                              "initiator": request.headers.get('eaid-next', "")
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{project_name}/campaigns/{version}/{occurrence}/tickets/"
            "{ticket_reference}/scenarios/{scenario_id}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_update_campaign_ticket_scenario_status(project_name: str,
                                                       version: str,
                                                       occurrence: str,
                                                       ticket_reference: str,
                                                       scenario_id: str,
                                                       updated_status: dict,
                                                       request: Request):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        result = await db_set_campaign_ticket_scenario_status(project_name,
                                                              version,
                                                              occurrence,
                                                              ticket_reference,
                                                              scenario_id,
                                                              updated_status["new_status"])
        log_message(result)

        return templates.TemplateResponse("void.html",
                                          {"request": request},
                                          headers={
                                              "hx-trigger": request.headers.get("eaid-next", "")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/"
            "{ticket_reference}/scenarios/{scenario_id}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_update_campaign_ticket_scenario_update_form(project_name: str,
                                                            version: str,
                                                            occurrence: str,
                                                            ticket_reference: str,
                                                            scenario_id: str,
                                                            request: Request):
    """Admin or user can update the scenario_internal_id status"""
    try:
        if not is_updatable(request, tuple()):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        scenario = await db_get_campaign_ticket_scenario(project_name,
                                                         version,
                                                         occurrence,
                                                         ticket_reference,
                                                         scenario_id)
        return templates.TemplateResponse("forms/campaign_scenario_status.html",
                                          {"project_name": project_name,
                                           "project_name_alias": provide(project_name),
                                           "version": version,
                                           "occurrence": occurrence,
                                           "ticket_reference": ticket_reference,
                                           "next": request.headers.get('eaid-next', ""),
                                           "scenario": scenario,
                                           "statuses": [status.value for status in
                                                        ScenarioStatusEnum],
                                           "request": request})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.delete("/{project_name}/campaigns/{version}/{occurrence}/tickets/"
               "{ticket_reference}/scenarios/{scenario_id}",
               tags=["Front - Campaign"],
               include_in_schema=False)
async def front_delete_campaign_ticket_scenario(project_name: str,
                                                version: str,
                                                occurrence: str,
                                                ticket_reference: str,
                                                scenario_id: str,
                                                request: Request):
    """Admin or user can update the scenario_internal_id status"""
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        await db_delete_campaign_ticket_scenario(project_name,
                                                 version,
                                                 occurrence,
                                                 ticket_reference,
                                                 scenario_id)
        return templates.TemplateResponse('void.html',
                                          {"request": request},
                                          headers={
                                              "HX-Trigger": request.headers.get('eaid-next', "")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def add_scenarios_to_ticket(project_name: str,
                                  version: str,
                                  occurrence: str,
                                  ticket_reference: str,
                                  element: dict,
                                  request: Request):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        valid = "scenario_ids" in element
        if valid and not isinstance(element["scenario_ids"], list):
            element["scenario_ids"] = [element["scenario_ids"]]

        if valid:
            await db_put_campaign_ticket_scenarios(project_name,
                                                   version,
                                                   occurrence,
                                                   ticket_reference,
                                                   [Scenarios(**element)])
        return templates.TemplateResponse('void.html',
                                          {"request": request},
                                          headers={
                                              "HX-Trigger": request.headers.get('eaid-next', "")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets",
            tags=["Front - Campaign"],
            include_in_schema=False
            )
async def front_campaign_version_tickets(project_name,
                                         version,
                                         occurrence,
                                         request: Request):
    try:
        if not is_updatable(request, tuple()):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        requested = request.headers.get("eaid-request", "")
        if requested == "FORM":
            tickets = await get_tickets_not_in_campaign(project_name, version, occurrence)
            return templates.TemplateResponse("forms/link_tickets_to_campaign.html",
                                              {
                                                  "request": request,
                                                  "project_name": project_name,
                                                  "project_name_alias": provide(project_name),
                                                  "version": version,
                                                  "occurrence": occurrence,
                                                  "tickets": tickets
                                              })
        else:
            # TODO: return the accordion table for the campaign (ease the refresh process)
            pass
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/campaigns/{version}/{occurrence}/tickets",
             tags=["Front - Campaign"],
             include_in_schema=False
             )
async def front_campaign_add_tickets(project_name: str,
                                     version: str,
                                     occurrence: str,
                                     request: Request,
                                     body: dict):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        await add_tickets_to_campaign(project_name, version, occurrence, body)
        # TODO capture header and send empty response with headers
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={
                                              "HX-Trigger": request.headers.get("eaid-next", "")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/campaigns/{version}/{occurrence}/results",
            tags=["Front - Campaign"],
            include_in_schema=False
            )
async def front_campaign_occurrence_status(project_name: str,
                                           version: str,
                                           occurrence: str,
                                           request: Request):
    try:
        result = await rs_retrieve_file(f"file:{provide(project_name)}:{version}:"
                                        f"{occurrence}:scenarios:map:text/html")
        if result is None:
            test_results = TestResults(
                REGISTERED_STRATEGY[RestTestResultCategoryEnum.SCENARIOS][
                    RestTestResultRenderingEnum.MAP],
                REGISTERED_OUTPUT[RestTestResultRenderingEnum.MAP][RestTestResultHeaderEnum.HTML])
            result = await test_results.render(project_name, version, occurrence)
            await rs_record_file(f"file:{provide(project_name)}:{version}:"
                                 f"{occurrence}:scenarios:map:text/html",
                                 result)
        return templates.TemplateResponse("frame.html",
                                          {
                                              "request": request,
                                              "link": f"{request.base_url}static/{result}"
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/campaigns/{version}/{occurrence}/results",
             tags=["Front - Campaign"],
             include_in_schema=False
             )
async def front_campaign_occurrence_snapshot_status(project_name: str,
                                                    version: str,
                                                    occurrence: str,
                                                    request: Request,
                                                    background_task: BackgroundTasks):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
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
        background_task.add_task(rs_invalidate_file,
                                 f"file:{provide(project_name)}:{version}:{occurrence}:*")
        return templates.TemplateResponse("back_message.html",
                                          {
                                              "request": request,
                                              "highlight": "Your request has been taken in "
                                                           "account.",
                                              "sequel": " The application is processing data.",
                                              "advise": f"You might see the status for "
                                                        f"{test_result_uuid}."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/campaigns/{version}/{occurrence}/deliverables",
            tags=["Front - Campaign"],
            include_in_schema=False
            )
async def front_campaign_occurrence_deliverables(project_name: str,
                                                 version: str,
                                                 occurrence: str,
                                                 request: Request,
                                                 deliverable_type: DeliverableTypeEnum =
                                                 DeliverableTypeEnum.TEST_PLAN,
                                                 ticket_ref: str = None):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
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

        return templates.TemplateResponse("download_link.html",
                                          {
                                              "request": request,
                                              "link": f"{request.base_url}static/{filename}"
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
