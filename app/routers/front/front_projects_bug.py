# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
from logging import getLogger
from typing import Optional

from fastapi import APIRouter, Security
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.pg_bugs import db_get_bug, db_update_bugs, get_bugs, insert_bug
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_versions import get_versions
from app.database.postgre.testcampaign import db_set_campaign_ticket_scenario_status
from app.schema.bugs_schema import BugTicket, UpdateBugTicket
from app.schema.error_code import ApplicationError
from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.status_enum import BugStatusEnum
from app.schema.users import User, UserLight
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")
logger = getLogger(__name__)


def __validate_from_scenario(version: str = None,
                             occurrence: int = None,
                             ticket_id: int = None,
                             scenario_id: int = None) -> bool:
    return (version is not None
            and occurrence is not None
            and ticket_id is not None
            and scenario_id is not None)


@router.get("/{project_name}/bugs",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_bugs(project_name: str,
                             request: Request,
                             display_all: Optional[str] = None,
                             version: str = None,
                             occurrence: str = None,
                             ticket_reference: str = None,
                             scenario_internal_id: str = None,
                             user: User = Security(front_authorize, scopes=["admin", "user"])
                             ) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        requested_item: str = request.headers.get("eaid-request", "")
        if requested_item is None:
            projects = await registered_projects()
            return templates.TemplateResponse("bugs.html",
                                              {
                                                  "request": request,
                                                  "projects": projects,
                                                  "display_closed": display_all,
                                                  "project_name": project_name,
                                                  "project_name_alias": provide(project_name)
                                              })

        elif requested_item.casefold() == "FORM".casefold():
            # Use query param to pre-populate the bug data
            if __validate_from_scenario(version, occurrence, ticket_reference, scenario_internal_id):
                # await scenario failure
                await db_set_campaign_ticket_scenario_status(project_name,
                                                                      version,
                                                                      occurrence,
                                                                      ticket_reference,
                                                                      scenario_internal_id,
                                                                      "waiting fix")
                versions = [version, ]
                test = {"occurrence": occurrence,
                        "ticket_reference": ticket_reference,
                        "scenario_internal_id": scenario_internal_id}
            else:
                versions = await get_versions(project_name)
                test = None
            return templates.TemplateResponse("forms/add_bug.html",
                                              {
                                                  "request": request,
                                                  "versions": versions,
                                                  "project_name": project_name,
                                                  "project_name_alias": provide(project_name),
                                                  "criticality": [f"{crit}" for crit in
                                                                  BugCriticalityEnum],
                                                  "test": test
                                              },
                                              headers={"hx-retarget": "#modals-here"})

        elif requested_item.casefold() == "TABLE".casefold():
            if display_all == "on".casefold():
                bugs, count = await get_bugs(project_name)
            else:
                bugs, count = await get_bugs(project_name,
                                             status=[BugStatusEnum.open, BugStatusEnum.fix_ready])
            return templates.TemplateResponse("tables/bug_table.html",
                                              {"request": request,
                                               "bugs": bugs,
                                               "display_closed": display_all,
                                               "project_name": project_name,
                                               "project_name_alias": provide(project_name)}
                                              )
        else:
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "Unknown requested item",
                                                  "sequel": "provided.",
                                                  "advise": "Please reload the page."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/bugs",
             tags=["Front - Project"],
             include_in_schema=False)
async def record_bug(project_name: str,
                     body: BugTicket,
                     request: Request,
                     user: User = Security(front_authorize, scopes=["admin", "user"])
                     ) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        # complement_data = {"status": BugStatusEnum.open}
        body.serialize()
        res = await insert_bug(project_name, body)
        logger.info(repr(res))
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          },
                                          headers={
                                              "HX-Trigger": json.dumps({"modalClear": "", "form-refresh": ""})
                                          })
    except ValidationError as exception:
        logger.exception(repr(exception))
        message = ""
        for mess in json.loads(exception.json()):
            message = f"{message}{mess['loc'][-1]}: {mess['msg']}. "
        return templates.TemplateResponse("forms/add_bug.html",
                                          {
                                              "request": request,
                                              "versions": [body["version"]],
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "criticality": [f"{crit}" for crit in
                                                              BugCriticalityEnum],
                                              "posted": body,
                                              "message": message
                                          },
                                          headers={"HX-Retarget": "#modal",  # Retarget
                                                   "HX-Reswap": "beforeend"})
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/bugs/{internal_id}",
            tags=["Front - Project"],
            include_in_schema=False)
async def display_bug(project_name: str,
                      internal_id: str,
                      request: Request,
                      user: User = Security(front_authorize, scopes=["admin", "user"])
                      ) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        bug = await db_get_bug(project_name, internal_id)
        versions = await get_versions(project_name)
        return templates.TemplateResponse("forms/update_bug.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "versions": versions,
                                              "criticality": [f"{crit}" for crit in
                                                              BugCriticalityEnum],
                                              "bug": bug
                                          },
                                          headers={"hx-retarget": "#modals-here"})
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{project_name}/bugs/{internal_id}",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_update_bug(project_name: str,
                           internal_id: str,
                           body: UpdateBugTicket,
                           request: Request,
                           user: User = Security(front_authorize, scopes=["admin", "user"])
                           ) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        body.serialize()
        res = await db_update_bugs(project_name, internal_id, body)
        if isinstance(res, ApplicationError):
            raise Exception(res.message)
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          },
                                          headers={
                                              "HX-Trigger": json.dumps({"modalClear": "", "form-refresh": ""})
                                          })
    except Exception as exception:
        logger.exception(repr(exception))
        posted = await db_get_bug(project_name, internal_id)
        posted = {**posted.model_dump(), **body.model_dump()}
        versions = await get_versions(project_name)
        return templates.TemplateResponse("forms/update_bug.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "versions": versions,
                                              "criticality": [f"{crit}" for crit in
                                                              BugCriticalityEnum],
                                              "bug": posted,
                                              "message": ("The update cannot be done. Ensure that the bug title is not "
                                                          "empty or does not exist for this project.")
                                          },
                                          headers={"HX-Retarget": "#modal",
                                                   "HX-Reswap": "beforeend"})


@router.patch("/{project_name}/bugs/{internal_id}",
              tags=["Front - Project"],

              include_in_schema=False)
async def front_update_bug_patch(project_name: str,
                                 internal_id: str,
                                 body: dict,
                                 request: Request,
                                 user: User = Security(front_authorize, scopes=["admin", "user"])
                                 ) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        res = await db_update_bugs(project_name, internal_id, UpdateBugTicket(**body))
        if isinstance(res, ApplicationError):
            raise Exception(res.message)
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          },
                                          headers={
                                              "HX-Trigger": request.headers.get('eaid-next', "")
                                          })
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)
