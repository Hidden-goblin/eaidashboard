# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter
from starlette.requests import Request

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import is_updatable
from app.database.postgre.pg_bugs import (db_get_bug,
                                          db_update_bugs,
                                          get_bugs,
                                          insert_bug)
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_versions import get_versions
from app.schema.bugs_schema import BugTicket, UpdateBugTicket
from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.utils.log_management import log_error, log_message
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/bugs",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_bugs(project_name: str,
                             request: Request,
                             display_all: Optional[str] = None):
    try:
        allowed = is_updatable(request, tuple())
        requested_item = request.headers.get("eaid-request", None)
        if request.headers.get("eaid-request", "") == "REDIRECT":
            return templates.TemplateResponse("void.html",
                                              {
                                                  "request": request
                                              },
                                              headers={
                                                  "HX-Redirect": f"/front/v1/projects/"
                                                                 f"{project_name}/bugs"})
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
        elif requested_item.casefold() == "FORM".casefold() and allowed:
            versions = await get_versions(project_name)
            return templates.TemplateResponse("forms/add_bug.html",
                                              {
                                                  "request": request,
                                                  "versions": versions,
                                                  "project_name": project_name,
                                                  "project_name_alias": provide(project_name),
                                                  "criticality": [f"{crit}" for crit in
                                                                  BugCriticalityEnum]
                                              })
        elif requested_item.casefold() == "TABLE".casefold() and allowed:
            if display_all == "on".casefold():
                bugs = await get_bugs(project_name)
            else:
                bugs = await get_bugs(project_name, status=BugStatusEnum.open)
            return templates.TemplateResponse("tables/bug_table.html",
                                              {"request": request,
                                               "bugs": bugs,
                                               "display_closed": display_all,
                                               "project_name": project_name,
                                               "project_name_alias": provide(project_name)}
                                              )
        elif allowed:
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "Unknown requested item",
                                                  "sequel": "provided.",
                                                  "advise": "Please reload the page."
                                              })
        else:
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/bugs",
             tags=["Front - Project"],
             include_in_schema=False)
async def record_bug(project_name: str,
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
                                              })
        complement_data = {"status": BugStatusEnum.open}
        res = await insert_bug(project_name, BugTicket(**body, **complement_data))
        log_message(res)
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
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/bugs/{internal_id}",
            tags=["Front - Project"],
            include_in_schema=False)
async def display_bug(project_name: str,
                      internal_id: str,
                      request: Request):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              })
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
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{project_name}/bugs/{internal_id}",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_update_bug(project_name: str,
                           internal_id: str,
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
        bug = UpdateBugTicket(**body)
        res = await db_update_bugs(project_name, internal_id, bug)
        log_message(res)
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
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.patch("/{project_name}/bugs/{internal_id}",
              tags=["Front - Project"],
              include_in_schema=False)
async def front_update_bug_patch(project_name: str,
                                 internal_id: str,
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
        res = await db_update_bugs(project_name, internal_id, UpdateBugTicket(**body))
        log_message(res)
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
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
