# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
import logging

from fastapi import APIRouter, Form
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authentication import authenticate_user, create_access_token, invalidate_token
from app.database.authorization import is_updatable
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_tickets import get_ticket, get_tickets, update_ticket
from app.database.postgre.pg_versions import dashboard as db_dash
from app.database.postgre.pg_versions import get_version, refresh_version_stats
from app.schema.ticket_schema import UpdatedTicket
from app.utils.log_management import log_error, log_message
from app.utils.project_alias import provide

router = APIRouter()


@router.get("/",
            response_class=HTMLResponse,
            include_in_schema=False,
            tags=["Front - Dashboard"])
async def dashboard(request: Request):
    try:
        if not is_updatable(request, ()):
            request.session.pop("token", None)
        if request.headers.get("eaid-request", None) is None:
            return templates.TemplateResponse("dashboard.html",
                                              {"request": request})
        if request.headers.get("eaid-request", None) == "table":
            return templates.TemplateResponse("tables/dashboard_table.html",
                                              {"request": request,
                                               "project_version": await db_dash()})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/versions/{project_version}/tickets",
            response_class=HTMLResponse,
            tags=["Front - Utils"],
            include_in_schema=False)
async def project_version_tickets(request: Request, project_name, project_version):
    try:
        return (
            templates.TemplateResponse(
                "ticket_view.html",
                {
                    "request": request,
                    "tickets": await get_tickets(project_name, project_version),
                    "project_name": project_name,
                    "project_name_alias": provide(project_name),
                    "project_version": project_version,
                },
            )
            if is_updatable(request, tuple())
            else templates.TemplateResponse(
                "error_message.html",
                {
                    "request": request,
                    "highlight": "You are not authorized",
                    "sequel": " to perform this action.",
                    "advise": "Try to log again.",
                },
                headers={"HX-Retarget": "#messageBox"},
            )
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.delete("/clear",
               response_class=HTMLResponse,
               tags=["Front - Utils"],
               include_in_schema=False)
async def return_void(request: Request):
    return templates.TemplateResponse("void.html",
                                      {"request": request},
                                      headers={
                                          "HX-Trigger": request.headers.get('eaid-next', "")
                                      })


@router.get("/login",
            response_class=HTMLResponse,
            tags=["Front - Login"],
            include_in_schema=False
            )
async def login(request: Request):
    try:
        return templates.TemplateResponse("forms/login_modal.html",
                                          {"request": request,
                                           "message": None})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post("/login",
             response_class=HTMLResponse,
             tags=["Front - Login"],
             include_in_schema=False)
async def post_login(request: Request,
                     username: str = Form(...),
                     password: str = Form(...)
                     ):
    try:
        sub, scopes = authenticate_user(username, password)
        if sub is None:
            raise Exception("Unrecognized credentials")
        access_token = create_access_token(
            data={"sub": sub,
                  "scopes": scopes})
        request.session["token"] = access_token
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={"HX-Trigger": "modalClear",
                                                   "HX-Trigger-After-Swap": json.dumps(
                                                       {"navRefresh": '',
                                                        "update-dashboard": ""})}
                                          )
    except Exception as exception:
        log_error(repr(exception))
        return templates.TemplateResponse("forms/login_modal.html",
                                          {"request": request,
                                           "message": "\n".join(exception.args),
                                           "username": username},
                                          headers={"HX-Retarget": "#modal",
                                                   "HX-Reswap": "beforeend"}
                                          )


@router.delete("/login",
               response_class=HTMLResponse,
               tags=["Front - Login"],
               include_in_schema=False)
async def logout(request: Request):
    try:
        if is_updatable(request, ("admin", "user")):
            invalidate_token(request.session["token"])
        request.session.clear()
        return templates.TemplateResponse("void.html",
                                          {"request": request},
                                          headers={"HX-Trigger": json.dumps({"navRefresh": '',
                                                                             "update-dashboard":
                                                                                 ""})}
                                          )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/versions/{project_version}/tickets/{reference}/edit",
            response_class=HTMLResponse,
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_ticket_edit(request: Request, project_name, project_version, reference):
    try:
        return (
            templates.TemplateResponse(
                "ticket_row_edit.html",
                {
                    "request": request,
                    "ticket": await get_ticket(
                        project_name, project_version, reference
                    ),
                    "project_name": project_name,
                    "project_name_alias": provide(project_name),
                    "project_version": project_version,
                },
            )
            if is_updatable(request, tuple())
            else templates.TemplateResponse(
                "error_message.html",
                {
                    "request": request,
                    "highlight": "You are not authorized",
                    "sequel": " to perform this action.",
                    "advise": "Try to log again.",
                },
                headers={"HX-Retarget": "#messageBox"},
            )
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{project_name}/versions/{project_version}/tickets/{reference}",
            response_class=HTMLResponse,
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_ticket(request: Request, project_name, project_version, reference):
    try:
        return (
            templates.TemplateResponse(
                "ticket_row.html",
                {
                    "request": request,
                    "ticket": await get_ticket(
                        project_name, project_version, reference
                    ),
                    "project_name": project_name,
                    "project_name_alias": provide(project_name),
                    "project_version": project_version,
                },
            )
            if is_updatable(request, tuple())
            else templates.TemplateResponse(
                "error_message.html",
                {
                    "request": request,
                    "highlight": "You are not authorized",
                    "sequel": " to perform this action.",
                    "advise": "Try to log again.",
                },
                headers={"HX-Retarget": "#messageBox"},
            )
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{project_name}/versions/{project_version}/tickets/{reference}",
            response_class=HTMLResponse,
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_update_ticket(request: Request,
                                        project_name: str,
                                        project_version: str,
                                        reference: str,
                                        body: dict,
                                        background_task: BackgroundTasks):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You're not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try reconnect",
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        # TODO check if a refactor might enhance readability
        res = await update_ticket(project_name,
                                  project_version,
                                  reference,
                                  UpdatedTicket(description=body["description"],
                                                status=body["status"]))
        if not res.acknowledged:
            logging.getLogger().error("Not done")
        background_task.add_task(refresh_version_stats, project_name, project_version)
        return templates.TemplateResponse("ticket_row.html",
                                          {"request": request,
                                           "ticket": await get_ticket(project_name,
                                                                      project_version,
                                                                      reference),
                                           "project_name": project_name,
                                           "project_name_alias": provide(project_name),
                                           "project_version": project_version},
                                          headers={"HX-Trigger": "update-dashboard"})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/front/v1/navigation",
            response_class=HTMLResponse,
            tags=["Front - Campaign"],
            include_in_schema=False
            )
async def get_navigation_bar(request: Request):
    projects = await registered_projects()
    return templates.TemplateResponse("navigation.html",
                                      {"request": request,
                                       "projects": projects or []}
                                      )


# @router.get("/testResults",
#             response_class=HTMLResponse,
#             tags=["Front - Campaign"],
#             include_in_schema=False)
# async def get_test_results(request: Request):
#     try:
#         if not is_updatable(request, tuple()):
#             return templates.TemplateResponse("error_message.html",
#                                               {
#                                                   "request": request,
#                                                   "highlight": "You are not authorized",
#                                                   "sequel": " to perform this action.",
#                                                   "advise": "Try to log again."
#                                               },
#                                               headers={"HX-Retarget": "#messageBox"})
#         projects = await registered_projects()
#         result = {project: await get_project_results(project) for project in projects}
#         return templates.TemplateResponse("test_results.html",
#                                           {"request": request,
#                                            "results": result})
#     except Exception as exception:
#         log_error(repr(exception))
#         return front_error_message(templates, request, exception)


@router.get("front/v1/projects/{project}/versions/{version}",
            response_class=HTMLResponse,
            tags=["Front - Campaign"],
            include_in_schema=False
            )
async def get_project_version(project: str,
                              version: str,
                              request: Request):
    try:
        if not is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You're not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try reconnect",
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
        version = get_version(project, version)
        log_message(repr(version))
        return templates.TemplateResponse("forms/update_version_modal.html",
                                          {
                                              "request": request,
                                              "version": repr(version)
                                          })
    except Exception as exception:
        return front_error_message(templates, request, exception)
