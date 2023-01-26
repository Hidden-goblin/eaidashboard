# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging

from fastapi import APIRouter, Form, HTTPException
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.conf import templates
from app.database.authentication import authenticate_user, create_access_token, invalidate_token
from app.database.authorization import is_updatable
from app.database.mongo.projects import registered_projects
from app.database.mongo.tickets import get_ticket, get_tickets, update_ticket, update_values
from app.database.mongo.versions import dashboard as db_dash
from app.schema.ticket_schema import UpdatedTicket
from app.utils.project_alias import provide

router = APIRouter()


@router.get("/",
            response_class=HTMLResponse,
            include_in_schema=False,
            tags=["Front - Dashboard"])
async def dashboard(request: Request):
    if not is_updatable(request, ()):
        request.session.pop("token", None)
    projects = await registered_projects()
    return templates.TemplateResponse("dashboard.html",
                                      {"request": request,
                                       "project_version": await db_dash(),
                                       "projects": projects or []})


@router.get("/{project_name}/versions/{project_version}/tickets",
            response_class=HTMLResponse,
            tags=["Front - Utils"],
            include_in_schema=False)
async def project_version_tickets(request: Request, project_name, project_version):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    return templates.TemplateResponse("ticket_view.html",
                                      {"request": request,
                                       "tickets": await get_tickets(project_name, project_version),
                                       "project_name": project_name,
                                       "project_name_alias": provide(project_name),
                                       "project_version": project_version})


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
    return templates.TemplateResponse("login_modal.html",
                                      {"request": request})


@router.post("/login",
             response_class=HTMLResponse,
             tags=["Front - Login"],
             include_in_schema=False)
async def post_login(request: Request,
                     username: str = Form(...),
                     password: str = Form(...)
                     ):
    sub, scopes = authenticate_user(username, password)
    if sub is None:
        return HTTPException(401, detail="Unrecognized credentials")
    access_token = create_access_token(
        data={"sub": sub,
              "scopes": scopes})
    request.session["token"] = access_token
    return templates.TemplateResponse("void.html",
                                      {
                                          "request": request
                                      })


@router.delete("/login",
               response_class=HTMLResponse,
               tags=["Front - Login"],
               include_in_schema=False)
async def logout(request: Request):
    if is_updatable(request, ("admin", "user")):
        invalidate_token(request.session["token"])
    request.session.clear()
    return templates.TemplateResponse("void.html",
                                      {"request": request})


@router.get("/{project_name}/versions/{project_version}/tickets/{reference}/edit",
            response_class=HTMLResponse,
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_ticket_edit(request: Request, project_name, project_version, reference):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    return templates.TemplateResponse("ticket_row_edit.html",
                                      {"request": request,
                                       "ticket": await get_ticket(project_name,
                                                            project_version,
                                                            reference),
                                       "project_name": project_name,
                                       "project_name_alias": provide(project_name),
                                       "project_version": project_version})


@router.get("/{project_name}/versions/{project_version}/tickets/{reference}",
            response_class=HTMLResponse,
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_ticket(request: Request, project_name, project_version, reference):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    return templates.TemplateResponse("ticket_row.html",
                                      {"request": request,
                                       "ticket": await get_ticket(project_name,
                                                            project_version,
                                                            reference),
                                       "project_name": project_name,
                                       "project_name_alias": provide(project_name),
                                       "project_version": project_version})


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
    if not is_updatable(request, ("admin", "user")):
        # TODO unify to the error_message template
        return templates.TemplateResponse("modal_error.html",
                                          {"request": request,
                                           "message": "You're not authorized",
                                           "my_fetch": f"then fetch /{project_name}/versions/"
                                                       f"{project_version}/tickets as html "
                                                       f"put the result into #tickets "})
    # TODO check if a refactor might enhance readability
    res = await update_ticket(project_name,
                        project_version,
                        reference,
                        UpdatedTicket(description=body["description"], status=body["status"]))
    if not res.acknowledged:
        logging.getLogger().error("No done")
    background_task.add_task(update_values, project_name, project_version)
    return templates.TemplateResponse("ticket_row.html",
                                      {"request": request,
                                       "ticket": await get_ticket(project_name,
                                                            project_version,
                                                            reference),
                                       "project_name": project_name,
                                       "project_name_alias": provide(project_name),
                                       "project_version": project_version})


@router.get("/testResults",
            response_class=HTMLResponse,
            tags=["Front - Campaign"],
            include_in_schema=False)
async def get_test_results(request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    projects = await registered_projects()
    result = {project: await get_project_results(project) for project in projects}
    return templates.TemplateResponse("test_results.html",
                                      {"request": request,
                                       "results": result})
