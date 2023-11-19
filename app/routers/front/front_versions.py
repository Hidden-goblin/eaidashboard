# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import Security, Form, APIRouter
from psycopg.errors import UniqueViolation, CheckViolation
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_access_denied, front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.pg_campaigns_management import enrich_tickets_with_campaigns
from app.database.postgre.pg_projects import get_project, create_project_version
from app.database.postgre.pg_tickets import get_tickets, add_ticket
from app.database.postgre.pg_versions import get_version, update_version_data
from app.database.utils.transitions import authorized_transition
from app.schema.bugs_schema import UpdateVersion
from app.schema.project_schema import RegisterVersionResponse, RegisterVersion
from app.schema.status_enum import TicketType, StatusEnum
from app.schema.ticket_schema import ToBeTicket
from app.schema.users import User, UserLight
from app.utils.log_management import log_error, log_message
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/versions",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_versions(project_name: str,
                           request: Request,
                           user: User = Security(front_authorize, scopes=["admin", "user"])) -> HTMLResponse:
    """Retrieve the project's version

    SPEC: Only authenticated user can access project's version"""
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", "") == "FORM" and user.right(project_name) != "admin":
            return front_access_denied(templates, request)

        if request.headers.get("eaid-request", "") == "FORM" and user.right(project_name) == "admin":
            return templates.TemplateResponse("forms/add_version.html",
                                              {
                                                  "request": request,
                                                  "project_name": project_name,
                                                  "project_name_alias": provide(project_name)
                                              })
        if request.headers.get("eaid-request", "") == "table":
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
        return templates.TemplateResponse("versions.html",
                                          {
                                              "request": request,
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
                                  request: Request,
                                  user: User = Security(front_authorize, scopes=["admin", "user"])) -> HTMLResponse:
    """Retrieve """
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", "") == "FORM" and user.right(project_name) != "admin":
            return front_access_denied(templates, request)

        if request.headers.get("eaid-request", "") == "FORM" and user.right(project_name) == "admin":
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
                                body: dict,
                                user: User = Security(front_authorize,
                                                      scopes=["admin"])) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        result = await add_ticket(project_name, version, ToBeTicket(**body))
        if not isinstance(result,
                          RegisterVersionResponse):
            raise Exception(result.message)

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
                                 request: Request,
                                 user: User = Security(front_authorize,
                                                       scopes=["admin", "user"])) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    version = await get_version(project_name, version)
    try:
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


@router.post("/{project_name}/versions",
             tags=["Front - Project"],
             include_in_schema=False)
async def add_version(project_name: str,
                      request: Request,
                      version: str = Form(...),
                      user: User = Security(front_authorize, scopes=["admin"])
                      ) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        await create_project_version(project_name, RegisterVersion(version=version))
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={"HX-Trigger": "update-version-table"})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("front/v1/projects/{project}/versions/{version}",
            tags=["Front - Campaign"],
            include_in_schema=False
            )
async def get_project_version(project: str,
                              version: str,
                              request: Request,
                              user: User = Security(front_authorize,
                                                    scopes=["admin", "user"])) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        version = get_version(project, version)
        log_message(repr(version))
        return templates.TemplateResponse("forms/update_version_modal.html",
                                          {
                                              "request": request,
                                              "version": repr(version)
                                          })
    except Exception as exception:
        return front_error_message(templates, request, exception)
