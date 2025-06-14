# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

import datetime
import json

from fastapi import APIRouter, Form, Security
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_access_denied, front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.pg_campaigns_management import (
    campaign_failing_scenarios,
    create_campaign,
    retrieve_campaign,
    update_campaign_occurrence,
)
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_test_results import TestResults
from app.database.postgre.pg_test_results import insert_result as pg_insert_result
from app.database.postgre.pg_tickets_management import get_tickets_not_in_campaign
from app.database.postgre.pg_versions import get_versions
from app.database.postgre.testcampaign import (
    db_delete_campaign_ticket_scenario,
    db_get_campaign_ticket_scenario,
    db_get_campaign_ticket_scenarios,
    db_get_campaign_ticket_scenarios_status_count,
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
from app.schema.campaign_schema import CampaignPatch
from app.schema.error_code import ApplicationError
from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum
from app.schema.respository.feature_schema import Feature
from app.schema.rest_enum import (
    DeliverableTypeEnum,
    RestTestResultCategoryEnum,
    RestTestResultHeaderEnum,
    RestTestResultRenderingEnum,
)
from app.schema.users import User, UserLight
from app.utils.log_management import log_error, log_message
from app.utils.pages import page_numbering
from app.utils.project_alias import provide
from app.utils.report_generator import campaign_deliverable

router = APIRouter(prefix="/front/v1/projects")


@router.get(
    "/{project_name}/campaigns",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def front_project_management(
    project_name: str,
    request: Request,
    limit: int = 10,
    skip: int = 0,
    version: str = None,
    bug: int = None,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", "") == "table":
            return await front_project_table(
                project_name,
                request,
                limit,
                skip,
            )
        if request.headers.get("eaid-request", "") == "form" and user.right(project_name) == "admin":
            return await front_new_campaign_form(
                project_name,
                request,
            )

        if request.headers.get("eaid-request", "") == "form" and user.right(project_name) != "admin":
            return front_access_denied(
                templates,
                request,
            )

        if request.headers.get("eaid-request", "") == "failed-scenario":
            sc = campaign_failing_scenarios(project_name, version, bug_internal_id=bug)

            return templates.TemplateResponse(
                "selectors/failed_scenarios_selector.html",
                {
                    "request": request,
                    "scenarios": sc,
                    # Insert scenario reference
                },
            )

        return templates.TemplateResponse(
            "campaign.html",
            {
                "request": request,
                "campaigns": True,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def front_project_table(
    project_name: str,
    request: Request,
    limit: int = 10,
    skip: int = 0,
) -> HTMLResponse:
    try:
        campaigns, count = await retrieve_campaign(
            project_name,
            limit=limit,
            skip=skip,
        )
        pages, current_page = page_numbering(
            count,
            limit,
            skip,
        )
        return templates.TemplateResponse(
            "tables/campaign_table.html",
            {
                "request": request,
                "campaigns": campaigns,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "pages": pages,
                "current": current_page,
                "nav_bar": count >= limit,
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def front_new_campaign_form(
    project_name: str,
    request: Request,
) -> HTMLResponse:
    try:
        return templates.TemplateResponse(
            "forms/add_campaign.html",
            {
                "request": request,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "versions": await get_versions(project_name, True),
            },
            headers={"HX-Trigger": request.headers.get("eaid-next", "")},
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/{project_name}/campaigns",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def front_new_campaign(
    project_name: str,
    request: Request,
    version: str = Form(...),
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        await create_campaign(project_name, version)
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={"hx-trigger": request.headers.get("eaid-next", "")},
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/{project_name}/campaigns/scenarios",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_scenarios_selector(
    project_name: str,
    body: dict,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    # Todo: Check route. Should be /{project_name}/campaigns/{version}/{occurrence}/scenarios
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        scenarios, count = await db_project_scenarios(project_name, body["epic"], body["feature"])
        return templates.TemplateResponse(
            "forms/add_scenarios_selector.html",
            {
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "epic": body["epic"],
                "feature": body["feature"],
                "scenarios": scenarios,
                "request": request,
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_get_campaign(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", "") == "table":
            campaign = await db_get_campaign_tickets(
                project_name,
                version,
                occurrence,
            )
            return templates.TemplateResponse(
                "tables/campaign_board_table.html",
                {
                    "request": request,
                    "campaign": campaign,
                    "project_name": project_name,
                    "version": version,
                    "occurrence": occurrence,
                },
            )
        if request.headers.get("eaid-request", "") == "form":
            campaign = await get_campaign_content(
                project_name,
                version,
                occurrence,
                True,
            )
            return templates.TemplateResponse(
                "forms/update_campaign_occurrence.html",
                {
                    "request": request,
                    "campaign": campaign,
                    "statuses": CampaignStatusEnum.list(),
                    "project_name": project_name,
                    "version": version,
                    "occurrence": occurrence,
                    "update": False,
                },
            )

        campaign = await get_campaign_content(
            project_name,
            version,
            occurrence,
            True,
        )
        projects = await registered_projects()
        return templates.TemplateResponse(
            "campaign_board.html",
            {
                "request": request,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "version": version,
                "occurrence": occurrence,
                "campaign": campaign,
                "projects": projects,
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.patch(
    "/{project_name}/campaigns/{version}/{occurrence}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_update_campaign(
    project_name: str,
    version: str,
    occurrence: str,
    body: dict,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        # Do the treatment here
        res = await update_campaign_occurrence(
            project_name,
            version,
            occurrence,
            CampaignPatch(**body),
        )
        if isinstance(res, ApplicationError):
            raise Exception(f"{res.error}\n{res.message}")
            # Success
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": json.dumps({"modalClear": "", "form-delete": ""}),
            },
        )
    except Exception as exception:
        log_error("\n".join(exception.args))
        campaign = await get_campaign_content(
            project_name,
            version,
            occurrence,
            True,
        )
        return templates.TemplateResponse(
            "forms/update_campaign_occurrence.html",
            {
                "request": request,
                "project_name": project_name,
                "version": version,
                "occurrence": occurrence,
                "campaign": campaign,
                "statuses": CampaignStatusEnum.list(),
                "update": True,
                "message": "\n".join(
                    exception.args,
                ),
                # Add the error message
            },
            headers={
                "HX-Retarget": "#modal",  # Retarget
                "HX-Reswap": "beforeend",
            },
        )  # Change swap


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_get_campaign_ticket_add_scenario(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
    initiator: str = None,
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        epics, __ = await db_project_epics(project_name)
        if epics:
            features, _count = await db_project_features(
                project_name,
                epics[0],
            )
            unique_features = {feature["name"] for feature in features}
        else:
            unique_features = set()
        return templates.TemplateResponse(
            "forms/add_scenarios.html",
            {
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "version": version,
                "occurrence": occurrence,
                "request": request,
                "ticket_reference": ticket_reference,
                "epics": epics,
                "features": unique_features,
                "initiator": request.headers.get("eaid-next", ""),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}/scenarios",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_get_campaign_ticket(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", "") == "statistics":
            stats = await db_get_campaign_ticket_scenarios_status_count(
                project_name,
                version,
                occurrence,
                ticket_reference,
            )
            return templates.TemplateResponse(
                "formatting/ticket_scenarios_count.html",
                {
                    "request": request,
                    "statistics": stats,
                },
            )

        scenarios = await db_get_campaign_ticket_scenarios(
            project_name,
            version,
            occurrence,
            ticket_reference,
        )
        return templates.TemplateResponse(
            "tables/ticket_scenarios.html",
            {
                "request": request,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "version": version,
                "occurrence": occurrence,
                "ticket_reference": ticket_reference,
                "scenarios": scenarios,
                "initiator": request.headers.get("eaid-next", ""),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}/scenarios/{scenario_internal_id}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_update_campaign_ticket_scenario_status(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
    scenario_internal_id: str,
    updated_status: dict,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        result = await db_set_campaign_ticket_scenario_status(
            project_name,
            version,
            occurrence,
            ticket_reference,
            scenario_internal_id,
            updated_status["new_status"],
        )
        log_message(result)

        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "modalClear": "",
                        f"{request.headers.get('eaid-next', '')}": "",
                    },
                ),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}/scenarios/{scenario_internal_id}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_update_campaign_ticket_scenario_update_form(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
    scenario_internal_id: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    """Admin or user can update the scenario_internal_id status"""
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        scenario = await db_get_campaign_ticket_scenario(
            project_name,
            version,
            occurrence,
            ticket_reference,
            scenario_internal_id,
        )
        return templates.TemplateResponse(
            "forms/campaign_scenario_status.html",
            {
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "version": version,
                "occurrence": occurrence,
                "ticket_reference": ticket_reference,
                "scenario": scenario,
                "statuses": [status.value for status in ScenarioStatusEnum],
                "next": request.headers.get("eaid-next", ""),
                "request": request,
            },
            headers={"hx-retarget": "#modals-here"},
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.delete(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}/scenarios/{scenario_internal_id}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_delete_campaign_ticket_scenario(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
    scenario_internal_id: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    """Admin or user can update the scenario_internal_id status"""
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        await db_delete_campaign_ticket_scenario(
            project_name,
            version,
            occurrence,
            ticket_reference,
            scenario_internal_id,
        )
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": request.headers.get("eaid-next", ""),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def add_scenarios_to_ticket(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
    element: Feature,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        await db_put_campaign_ticket_scenarios(
            project_name,
            version,
            occurrence,
            ticket_reference,
            [
                element,
            ],
        )
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": request.headers.get("eaid-next", ""),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_campaign_version_tickets(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        requested = request.headers.get("eaid-request", "")
        if requested == "FORM":
            tickets = await get_tickets_not_in_campaign(
                project_name,
                version,
                occurrence,
            )
            return templates.TemplateResponse(
                "forms/link_tickets_to_campaign.html",
                {
                    "request": request,
                    "project_name": project_name,
                    "project_name_alias": provide(project_name),
                    "version": version,
                    "occurrence": occurrence,
                    "tickets": tickets,
                },
            )
        else:
            # TODO: return the accordion table for the campaign (ease the refresh process)
            pass
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/{project_name}/campaigns/{version}/{occurrence}/tickets",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_campaign_add_tickets(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    body: dict,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        await add_tickets_to_campaign(
            project_name,
            version,
            occurrence,
            body,
        )
        # TODO capture header and send empty response with headers
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": request.headers.get("eaid-next", ""),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/results",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_campaign_occurrence_status(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        result = rs_retrieve_file(f"file:{provide(project_name)}:{version}:{occurrence}:scenarios:map:text/html")
        if result is None:
            test_results = TestResults(
                REGISTERED_STRATEGY[RestTestResultCategoryEnum.SCENARIOS][RestTestResultRenderingEnum.MAP],
                REGISTERED_OUTPUT[RestTestResultRenderingEnum.MAP][RestTestResultHeaderEnum.HTML],
            )
            result = await test_results.render(
                project_name,
                version,
                occurrence,
            )
            rs_record_file(
                f"file:{provide(project_name)}:{version}:{occurrence}:scenarios:map:text/html",
                result,
            )
        return templates.TemplateResponse(
            "frame.html",
            {
                "request": request,
                "link": f"{request.base_url}static/{result}",
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/{project_name}/campaigns/{version}/{occurrence}/results",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_campaign_occurrence_snapshot_status(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    background_task: BackgroundTasks,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        result = await register_manual_campaign_result(
            project_name,
            version,
            occurrence,
        )
        if isinstance(result, ApplicationError):
            raise Exception(result.message)
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
        background_task.add_task(
            rs_invalidate_file,
            f"file:{provide(project_name)}:{version}:{occurrence}:*",
        )
        return templates.TemplateResponse(
            "back_message.html",
            {
                "request": request,
                "highlight": "Your request has been taken in account.",
                "sequel": " The application is processing data.",
                "advise": f"You might see the status for {result.result_uuid}.",
            },
            headers={"HX-Retarget": "#messageBox"},
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/campaigns/{version}/{occurrence}/deliverables",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def front_campaign_occurrence_deliverables(
    project_name: str,
    version: str,
    occurrence: str,
    request: Request,
    deliverable_type: DeliverableTypeEnum = DeliverableTypeEnum.TEST_PLAN,
    ticket_ref: str = None,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
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
            rs_record_file(key, filename)

        return templates.TemplateResponse(
            "download_link.html",
            {
                "request": request,
                "link": f"{request.base_url}static/{filename}",
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
