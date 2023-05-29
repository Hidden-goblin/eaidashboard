# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import APIRouter, Form
from psycopg.errors import CheckViolation, UniqueViolation
from starlette.requests import Request

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import is_updatable
from app.database.postgre.pg_campaigns_management import enrich_tickets_with_campaigns
from app.database.postgre.pg_projects import create_project_version, get_project, register_project, registered_projects
from app.database.postgre.pg_tickets import add_ticket, get_tickets
from app.database.postgre.pg_versions import get_version, update_version_data
from app.database.postgre.testrepository import db_project_epics, db_project_features
from app.database.utils.transitions import authorized_transition
from app.schema.bugs_schema import UpdateVersion
from app.schema.project_schema import RegisterProject, RegisterVersion
from app.schema.status_enum import StatusEnum, TicketType
from app.schema.ticket_schema import ToBeTicket
from app.utils.log_management import log_error, log_message
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get("",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project(request: Request):
    try:
        if not is_updatable(request, ("admin",)):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        if request.headers.get("eaid-request") == "FORM":
            return templates.TemplateResponse("forms/create_project.html",
                                              {"request": request,
                                               "name": None,
                                               "error_message": ""})

    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("",
             tags=["Front - Project"],
             include_in_schema=False)
async def front_create_project(body: RegisterProject,
                               request: Request):
    try:
        if not is_updatable(request, ("admin",)):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        log_message(body)
        await register_project(body.name)
        return templates.TemplateResponse("void.html",
                                          {"request": request},
                                          headers={"HX-Trigger": "modalClear",
                                                   "HX-Trigger-After-Swap": "navRefresh"})
    except Exception as exception:
        log_error("\n".join(exception.args))
        return templates.TemplateResponse("forms/create_project.html",
                                          {
                                              "request": request,
                                              "name": body.name,
                                              "message": "\n".join(exception.args)
                                          },
                                          headers={"HX-Retarget": "#modal",
                                                   "HX-Reswap": "beforeend"})


@router.get("/{project_name}",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_management(project_name: str,
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
        # TODO refactor with headers
        if request.headers.get("eaid-request", "") == "REDIRECT":
            return templates.TemplateResponse("void.html",
                                              {
                                                  "request": request
                                              },
                                              headers={
                                                  "HX-Redirect": f"/front/v1/projects/"
                                                                 f"{project_name}"})
        _versions = await get_project(project_name, None)
        versions = [{"value": item["version"], "status": item["status"]} for item in
                    _versions["future"]]
        versions.extend(
            [{"value": item["version"], "status": item["status"]} for item in _versions["current"]])
        versions.extend(
            [{"value": item["version"], "status": item["status"]} for item in
             _versions["archived"]])
        projects = await registered_projects()
        return templates.TemplateResponse("project.html",
                                          {
                                              "request": request,
                                              "versions": versions,
                                              "projects": projects,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/versions",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_versions(project_name: str,
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
        _versions = await get_project(project_name, None)
        versions = [{"value": item["version"], "status": item["status"]} for item in
                    _versions["future"]]
        versions.extend(
            [{"value": item["version"], "status": item["status"]} for item in _versions["current"]])
        versions.extend(
            [{"value": item["version"], "status": item["status"]} for item in
             _versions["archived"]])
        return templates.TemplateResponse("tables/project_version.html",
                                          {
                                              "request": request,
                                              "versions": versions,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/versions/{version}",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_version_tickets(project_name: str,
                                  version: str,
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
        if request.headers.get("eaid-request", "") == "FORM":
            return templates.TemplateResponse("forms/add_ticket.html",
                                              {
                                                  "request": request,
                                                  "project_name": project_name,
                                                  "project_name_alias": provide(project_name),
                                                  "version": version,
                                                  "status": [status.value for status in TicketType]
                                              })
        if request.headers.get("eaid-request", "") == "versionUpdate":
            version = await get_version(project_name, version)
            log_message(repr(version))
            return templates.TemplateResponse("forms/update_version_modal.html",
                                              {
                                                  "request": request,
                                                  "project_name": project_name,
                                                  "version": version,
                                                  "transitions": authorized_transition[StatusEnum(
                                                      version.status)]
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
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/versions/{version}",
             tags=["Front - Project"],
             include_in_schema=False)
async def add_ticket_to_version(project_name: str,
                                version: str,
                                request: Request,
                                body: dict):
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
        result = await add_ticket(project_name, version, ToBeTicket(**body))
        if not result.inserted_id:
            return "error"
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request,
                                          },
                                          headers={"HX-Trigger": f"reload-{version}"})
    except UniqueViolation as uv:
        log_error(','.join(uv.args))
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": f"Ticket with {body.get('reference')} "
                                                           f"reference already exist in "
                                                           f"{project_name} ",
                                              "sequel": " so you cannot record it.",
                                              "advise": "Check the reference or the version."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{project_name}/versions/{version}",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_version_update(project_name: str,
                                 version: str,
                                 body: dict,
                                 request: Request):
    version = await get_version(project_name, version)
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
        log_message(body)

        cleaned_body = {key: value for key, value in body.items() if value}
        await update_version_data(project_name, version.version, UpdateVersion(**cleaned_body))

        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={"HX-Trigger": "modalClear",
                                                   "HX-Trigger-After-Swap": "update-dashboard"}
                                          )
    except CheckViolation as chk_violation:
        log_error(repr(chk_violation))
        return templates.TemplateResponse("forms/update_version_modal.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "version": version,
                                              "transitions": authorized_transition[StatusEnum(
                                                  version.status)],
                                              "message": "Started date could not be "
                                                         "after end forecast date"
                                          },
                                          headers={"HX-Retarget": "#modal",
                                                   "HX-Reswap": "beforeend"})
    except Exception as exception:
        log_error(repr(exception))
        return templates.TemplateResponse("forms/update_version_modal.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "version": version,
                                              "transitions": authorized_transition[StatusEnum(
                                                  version.status)],
                                              "message": ", ".join(exception.args)
                                          },
                                          headers={"HX-Retarget": "#modal",
                                                   "HX-Reswap": "beforeend"})


@router.get("/{project_name}/forms/version",
            tags=["Front - Project"],
            include_in_schema=False)
async def form_version(project_name: str,
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
        return templates.TemplateResponse("forms/add_version.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name)
                                          })
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/{project_name}/versions",
             tags=["Front - Project"],
             include_in_schema=False)
async def add_version(project_name: str,
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
                                                  "advise": "Try to log again."
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        await create_project_version(project_name, RegisterVersion(version=version))
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={"HX-Trigger": "update-version-table"})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def repository_dropdowns(project_name: str,
                               request: Request,
                               epic: str,
                               feature: str):
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
