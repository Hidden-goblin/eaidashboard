# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import datetime
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Response, Security
from starlette.background import BackgroundTasks
from starlette.requests import Request

from app.database.authorization import authorize_user
from app.database.postgre.pg_campaigns_management import create_campaign, retrieve_campaign
from app.database.postgre.pg_campaigns_management import update_campaign_occurrence as pg_update_campaign_occurrence
from app.database.postgre.pg_test_results import insert_result as pg_insert_result
from app.database.postgre.testcampaign import (
    db_get_campaign_ticket_scenario,
    db_get_campaign_ticket_scenarios,
    db_get_campaign_tickets,
    db_put_campaign_ticket_scenarios,
    db_set_campaign_ticket_scenario_status,
    get_campaign_content,
)
from app.database.postgre.testcampaign import fill_campaign as db_fill_campaign
from app.database.redis.rs_file_management import rs_record_file, rs_retrieve_file
from app.database.utils.object_existence import if_error_raise_http, project_version_raise
from app.database.utils.test_result_management import register_manual_campaign_result
from app.schema.base_schema import CreateUpdateModel
from app.schema.campaign_followup_schema import ComputeResultSchema
from app.schema.campaign_schema import (
    CampaignFull,
    CampaignLight,
    CampaignPatch,
    TicketScenarioCampaign,
    ToBeCampaign,
)
from app.schema.error_code import ErrorMessage
from app.schema.pg_schema import PGResult
from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum
from app.schema.respository.feature_schema import Feature
from app.schema.respository.scenario_schema import BaseScenario, ScenarioExecution
from app.schema.rest_enum import DeliverableTypeEnum
from app.schema.users import UpdateUser
from app.utils.log_management import log_error
from app.utils.report_generator import campaign_deliverable

router = APIRouter(prefix="/api/v1/projects")

log = logging.getLogger(__name__)


# Create blank campaign for version
@router.post(
    "/{project_name}/campaigns",
    tags=["Campaign"],
    description="Create a new campaign linked to a project-version."
    " Multiple occurrence of the same campaign can be created",
    response_model=CampaignLight,
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case), the version does not exist",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        422: {"model": ErrorMessage, "description": "Payload does not match the expected schema"},
        500: {"model": ErrorMessage, "description": "The server could not compute the result."},
    },
)
async def create_campaigns(
    project_name: str,
    campaign: ToBeCampaign,
    user: UpdateUser = Security(authorize_user, scopes=["admin"]),
) -> CampaignLight:
    await project_version_raise(
        project_name,
        campaign.version,
    )
    try:
        return await create_campaign(
            project_name,
            campaign.version,
        )
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp


# Link tickets & scenarios to campaign
# { "tickets": [{"epic", "feature", "scenario_id"}...]}
@router.put(
    "/{project_name}/campaigns/{version}/{occurrence}",
    tags=["Campaign"],
    description="Fill the campaign with ticket and scenarios",
    response_model=CreateUpdateModel,
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case),"
            " the version does not exist,"
            " the campaign-occurrence does not exist",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
    },
)
async def fill_campaign(
    project_name: str,
    version: str,
    occurrence: str,
    content: TicketScenarioCampaign,
    user: UpdateUser = Security(authorize_user, scopes=["admin"]),
) -> CreateUpdateModel:
    await project_version_raise(
        project_name,
        version,
    )
    try:
        campaign_ticket_id = await db_fill_campaign(
            project_name,
            version,
            occurrence,
            content,
        )
        if isinstance(campaign_ticket_id, CreateUpdateModel) and isinstance(content.scenarios, list | BaseScenario):
            scenarios = content.to_features(project_name)
            link_scenario = await db_put_campaign_ticket_scenarios(
                project_name,
                version,
                occurrence,
                content.ticket_reference,
                scenarios,
            )
            campaign_ticket_id += link_scenario

    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp

    return if_error_raise_http(campaign_ticket_id)


@router.get(
    "/{project_name}/campaigns",
    tags=["Campaign"],
    response_model=List[CampaignLight],
    description="""Retrieve campaign. Check before hand if project and version (if provided) exit.
     X-total-count header contains the total number of matches""",
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case), the version does not exist",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        500: {"model": ErrorMessage, "description": "Computation error"},
    },
)
async def get_campaigns(
    project_name: str,
    response: Response,
    version: str = None,
    status: CampaignStatusEnum = None,
    limit: int = 10,
    skip: int = 0,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> List[CampaignLight]:
    """
    Check project_name-version
    Gather campaigns with the status

    Args:
        project_name:
        response:
        version:
        status:
        limit:
        skip:
        user:

    Returns:

    """
    await project_version_raise(
        project_name,
        version,
    )
    try:
        campaigns, count = await retrieve_campaign(
            project_name,
            version,
            status,
            limit=limit,
            skip=skip,
        )
        response.headers["X-total-count"] = str(count)  # TODO check reason it doesn't work without cast
        return campaigns
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp


@router.patch(
    "/{project_name}/campaigns/{version}/{occurrence}",
    tags=["Campaign"],
    response_model=CampaignLight,
    description="Update the status of an occurrence",
    responses={
        400: {"model": ErrorMessage, "description": "version already exist"},
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case),"
            " the version does not exist,"
            " the campaign-occurrence does not exist",
        },
        422: {"model": ErrorMessage, "description": "The payload does not match the expected schema"},
    },
)
async def update_campaign_occurrence(
    project_name: str,
    version: str,
    occurrence: str,
    campaign_update: CampaignPatch,
    user: UpdateUser = Security(authorize_user, scopes=["admin"]),
) -> CampaignLight:
    # await project_version_raise(
    #     project_name,
    #     version,
    # )
    try:
        res = await pg_update_campaign_occurrence(
            project_name,
            version,
            occurrence,
            campaign_update,
        )
        if isinstance(res, PGResult):
            res = await get_campaign_content(project_name, version, occurrence, True)
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(res)


# Retrieve campaign for project


# Retrieve campaign for project-version
@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}",
    response_model=CampaignFull,
    tags=["Campaign"],
    description="Retrieve the full campaign",
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case),"
            " the version does not exist,"
            " the campaign-occurrence does not exist",
        },
        500: {"model": ErrorMessage, "description": "The server could not compute the result."},
    },
)
async def get_campaign(
    project_name: str,
    version: str,
    occurrence: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> CampaignFull:
    await project_version_raise(
        project_name,
        version,
    )
    try:
        result = await get_campaign_content(
            project_name,
            version,
            occurrence,
        )
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)


# Retrieve scenarios for project-version-campaign-ticket
@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets",
    tags=["Campaign"],
    response_model=CampaignFull,
    description="Retrieve a campaign tickets",
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Cannot find a campaign matching project, version, occurrence or scenario",
        },
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
)
async def get_campaign_tickets(
    project_name: str,
    version: str,
    occurrence: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> CampaignFull:
    await project_version_raise(
        project_name,
        version,
    )
    try:
        result = await db_get_campaign_tickets(
            project_name,
            version,
            occurrence,
        )
    except Exception as exp:
        raise HTTPException(500, repr(exp)) from exp
    return if_error_raise_http(result)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_ref}",
    tags=["Campaign"],
    description="Retrieve a campaign ticket",
    response_model=List[ScenarioExecution],
)
async def get_campaign_ticket(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_ref: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> List[ScenarioExecution]:
    try:
        result = await db_get_campaign_ticket_scenarios(
            project_name,
            version,
            occurrence,
            ticket_ref,
        )
    except Exception as exp:
        raise HTTPException(500, repr(exp))
    return if_error_raise_http(result)


@router.put(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_ref}",
    tags=["Campaign"],
    description="Add scenarios to a ticket",
    response_model=CreateUpdateModel,
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Cannot find a campaign matching project, version, occurrence or scenario",
        },
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
)
async def put_campaign_ticket_scenarios(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_ref: str,
    scenarios: List[Feature],
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> CreateUpdateModel:
    try:
        result = await db_put_campaign_ticket_scenarios(
            project_name,
            version,
            occurrence,
            ticket_ref,
            scenarios,
        )
    except Exception as exp:
        raise HTTPException(500, repr(exp))
    return if_error_raise_http(result)


# Retrieve scenario_internal_id for specific campaign and ticket
# Todo update to retrieve all details of the scenario
@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{reference}/scenarios/{scenario_id}",
    tags=["Campaign"],
    description="Retrieve a test scenario by its id. ",
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Cannot find a campaign matching project, version, occurrence or scenario",
        },
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
)
async def get_campaign_ticket_scenario(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
    scenario_id: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> dict:
    try:
        result = await db_get_campaign_ticket_scenario(
            project_name,
            version,
            occurrence,
            reference,
            scenario_id,
        )
    except Exception as exp:
        raise HTTPException(
            500,
            repr(exp),
        )
    return if_error_raise_http(result)


@router.put(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{reference}/scenarios/{scenario_internal_id}/status",
    tags=["Campaign"],
    description="Directly update the scenario status\n Check the destination status exists",
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Cannot find a campaign matching project, version, occurrence or scenario",
        },
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
)
async def update_campaign_ticket_scenario_status(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
    scenario_internal_id: str,
    new_status: ScenarioStatusEnum,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> dict:
    try:
        _status = await db_set_campaign_ticket_scenario_status(
            project_name,
            version,
            occurrence,
            reference,
            scenario_internal_id,
            new_status,
        )
    except Exception as exp:
        raise HTTPException(
            500,
            repr(exp),
        )
    return if_error_raise_http(_status)


@router.post(
    "/{project_name}/campaigns/{version}/{occurrence}",
    description="Generate the result for this particular occurrence i.e. capture the current state",
    tags=["Campaign"],
    responses={
        404: {
            "model": ErrorMessage,
            "description": "Cannot find a campaign matching project, version or occurrence",
        },
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
)
async def create_campaign_occurrence_result(
    project_name: str,
    version: str,
    occurrence: str,
    background_task: BackgroundTasks,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> str:
    try:
        result = await register_manual_campaign_result(
            project_name,
            version,
            occurrence,
        )
        if isinstance(result, ComputeResultSchema):
            background_task.add_task(
                pg_insert_result,
                datetime.datetime.now(),
                project_name,
                version,
                result.campaign_id,
                True,
                result.result_uuid,
                result.scenarios,
            )
            return result.result_uuid
    except Exception as exp:
        raise HTTPException(500, repr(exp))
    # noinspection PyTypeChecker
    return if_error_raise_http(result)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/deliverables",
    tags=["Campaign-Deliverables"],
)
async def retrieve_campaign_occurrence_deliverables(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    deliverable_type: DeliverableTypeEnum = DeliverableTypeEnum.TEST_PLAN,
    ticket_ref: str = None,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> str:
    try:
        if ticket_ref is not None:
            key = f"file:{project_name}:{version}:{occurrence}:{ticket_ref}:{deliverable_type.value}"
        else:
            key = f"file:{project_name}:{version}:{occurrence}:{deliverable_type.value}"
        filename = rs_retrieve_file(key)
        if filename is None:
            filename = await campaign_deliverable(
                project_name,
                version,
                occurrence,
                deliverable_type,
                ticket_ref,
            )
            if isinstance(filename, str):
                rs_record_file(
                    key,
                    filename,
                )
                filename = f"{request.base_url}static/{filename}"
    except Exception as exp:
        raise HTTPException(500, repr(exp)) from exp
    return if_error_raise_http(filename)
