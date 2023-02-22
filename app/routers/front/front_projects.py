# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import APIRouter, Form, HTTPException
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app import conf
from app.conf import templates
from app.database.authorization import is_updatable
if conf.MIGRATION_DONE:
    from app.database.postgre.pg_projects import (create_project_version,
                                                  get_project,
                                                  registered_projects)
    from app.database.postgre.pg_tickets import (add_ticket,
                                                 get_tickets,
                                                 update_values)
else:
    from app.database.mongo.projects import (create_project_version,
                                             get_project,
                                             registered_projects)
    from app.database.mongo.tickets import (add_ticket,
                                            get_tickets,
                                            update_values)
from app.database.postgre.pg_campaigns_management import enrich_tickets_with_campaigns
from app.database.postgre.testrepository import db_project_epics, db_project_features
from app.schema.project_schema import RegisterVersion
from app.schema.status_enum import TicketType
from app.schema.ticket_schema import ToBeTicket
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_management(project_name: str,
                                   request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    if request.headers.get("eaid-request", "") == "REDIRECT":
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={
                                              "HX-Redirect": f"/front/v1/projects/{project_name}"})
    _versions = await get_project(project_name, None)
    versions = [{"value": item["version"], "status": item["status"]} for item in _versions["future"]]
    versions.extend(
        [{"value": item["version"], "status": item["status"]} for item in _versions["current"]])
    versions.extend(
        [{"value": item["version"], "status": item["status"]} for item in _versions["archived"]])
    projects = await registered_projects()
    return templates.TemplateResponse("project.html",
                                      {
                                          "request": request,
                                          "versions": versions,
                                          "projects": projects,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name)
                                      })


@router.get("/{project_name}/versions",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_versions(project_name: str,
                           request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    _versions = await get_project(project_name, None)
    versions = [{"value": item["version"], "status": item["status"]} for item in
                _versions["future"]]
    versions.extend(
        [{"value": item["version"], "status": item["status"]} for item in _versions["current"]])
    versions.extend(
        [{"value": item["version"], "status": item["status"]} for item in _versions["archived"]])
    return templates.TemplateResponse("tables/project_version.html",
                                      {
                                          "request": request,
                                          "versions": versions,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name)
                                      })

@router.get("/{project_name}/versions/{version}",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_version_tickets(project_name: str,
                                  version: str,
                                  request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    if request.headers.get("eaid-request", "")  == "FORM":
        return templates.TemplateResponse("forms/add_ticket.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "version": version,
                                              "status": [status.value for status in TicketType]
                                          })
    tickets = await get_tickets(project_name, version)
    tickets = await enrich_tickets_with_campaigns(project_name, version, tickets)
    return templates.TemplateResponse("tables/version_tickets.html",
                                  {
                                      "request": request,
                                      "version": version,
                                      "project_name": project_name,
                                      "project_name_alias": provide(project_name),
                                      "tickets": tickets
                                  })


@router.post("/{project_name}/versions/{version}",
            tags=["Front - Project"],
            include_in_schema=False)
async def add_ticket_to_version(project_name: str,
                                version: str,
                                request: Request,
                                body: dict,
                                background_task: BackgroundTasks):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    result = await add_ticket(project_name,version, ToBeTicket(**body))
    if not result.inserted_id:
        return "error"
    background_task.add_task(update_values, project_name, version)
    return templates.TemplateResponse("void.html",
                                      {
                                          "request": request,
                                      },
                                      headers={"HX-Trigger": f"reload-{version}"})


@router.get("/{project_name}/forms/version",
            tags=["Front - Project"],
            include_in_schema=False)
async def form_version(project_name: str,
                       request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    return templates.TemplateResponse("forms/add_version.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name)
                                      })


@router.post("/{project_name}/forms/version",
             tags=["Front - Project"],
             include_in_schema=False)
async def add_version(project_name: str,
                      request: Request,
                      version: str = Form(...)
                      ):
    if not is_updatable(request, ("admin", "user")):
        raise HTTPException(status_code=403, detail="Not authorized")
    await create_project_version(project_name, RegisterVersion(version=version))
    return HTMLResponse("")


async def repository_dropdowns(project_name: str, request: Request, epic: str, feature: str):
    if epic is None and feature is None:
        epics = await db_project_epics(project_name)
        if epics:
            features = {feature["name"] for feature in await db_project_features(project_name,
                                                                                 epics[0])}
        else:
            features = set()
        return templates.TemplateResponse("selectors/epic_label_selectors.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "epics": epics,
                                              "features": features
                                          })
    if epic is not None and feature is None:
        features = {feature["name"] for feature in await db_project_features(project_name, epic)}
        return templates.TemplateResponse("selectors/feature_label_selectors.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "features": features
                                          })


async def repository_board(project_name, request, epic, feature, limit, skip):

    pass
