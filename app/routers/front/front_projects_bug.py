# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request

from app.conf import templates
from app.database.authorization import is_updatable
from app.database.mongo.bugs import db_get_bug, db_update_bugs, get_bugs, insert_bug, version_bugs
from app.database.mongo.versions import get_versions
from app.database.settings import registered_projects
from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.project_schema import BugTicket, UpdateBugTicket

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/bugs",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_bugs(project_name: str,
                             request: Request,
                             display_all: Optional[str] = None):
    allowed = is_updatable(request, tuple())
    requested_item = request.headers.get("eaid-request", None)
    if request.headers.get("eaid-request", "") == "REDIRECT":
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={"HX-Redirect": f"/front/v1/projects/{project_name}/bugs"})
    if requested_item is None:
        projects = await registered_projects()
        return templates.TemplateResponse("bugs.html",
                                          {
                                              "request": request,
                                              "projects": projects,
                                              "display_closed": display_all,
                                              "project_name": project_name
                                          })
    elif requested_item.casefold() == "FORM".casefold() and allowed:
        versions = await get_versions(project_name)
        return templates.TemplateResponse("forms/add_bug.html",
                                          {
                                              "request": request,
                                              "versions": versions,
                                              "project_name": project_name,
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
                                           "project_name": project_name}
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

@router.post("/{project_name}/bugs",
             tags=["Front - Project"],
             include_in_schema=False)
async def record_bug(project_name: str,
                     body: dict,
                     request: Request,
                     background_task: BackgroundTasks):
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
    background_task.add_task(version_bugs,project_name, body["version"])
    return templates.TemplateResponse("void.html",
                                      {
                                          "request": request,
                                          "project_name": project_name
                                      },
                                      headers={
                                          "HX-Trigger": request.headers.get('eaid-next', "")
                                      })

@router.get("/{project_name}/bugs/{internal_id}",
             tags=["Front - Project"],
             include_in_schema=False)
async def display_bug(project_name: str,
                      internal_id: str,
                      request: Request):
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
                                          "versions": versions,
                                          "criticality": [f"{crit}" for crit in
                                                          BugCriticalityEnum],
                                          "bug": bug
                                      })

@router.put("/{project_name}/bugs/{internal_id}",
             tags=["Front - Project"],
             include_in_schema=False)
async def front_update_bug(project_name: str,
                           internal_id: str,
                           body: dict,
                           request: Request,
                           background_task: BackgroundTasks):
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
    background_task.add_task(version_bugs, project_name, body["version"])
    return templates.TemplateResponse("void.html",
                                      {
                                          "request": request,
                                          "project_name": project_name
                                      },
                                      headers={
                                          "HX-Trigger": request.headers.get('eaid-next', "")
                                      })

@router.patch("/{project_name}/bugs/{internal_id}",
             tags=["Front - Project"],
             include_in_schema=False)
async def front_update_bug_patch(project_name: str,
                           internal_id: str,
                           body: dict,
                           request: Request,
                           background_task: BackgroundTasks):
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
    background_task.add_task(version_bugs, project_name, body["version"])
    return templates.TemplateResponse("void.html",
                                      {
                                          "request": request,
                                          "project_name": project_name
                                      },
                                      headers={
                                          "HX-Trigger": request.headers.get('eaid-next', "")
                                      })