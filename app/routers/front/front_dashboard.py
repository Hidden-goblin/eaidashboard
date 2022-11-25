# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
import urllib.parse
from base64 import decode

from fastapi import APIRouter, Form, HTTPException
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.conf import templates
from app.database.authentication import authenticate_user, create_access_token, invalidate_token
from app.database.authorization import is_updatable
from app.database.projects import get_project_results
from app.database.settings import registered_projects
from app.database.tickets import get_ticket, get_tickets, update_ticket, update_values
from app.database.versions import dashboard as db_dash
from app.schema.project_schema import UpdatedTicket

router = APIRouter()


@router.get("/",
            response_class=HTMLResponse,
            include_in_schema=False,
            tags=["Front - Dashboard"])
async def dashboard(request: Request):
    if not is_updatable(request, ()):
        request.session.pop("token", None)
    projects = registered_projects()
    return templates.TemplateResponse("dashboard.html",
                                      {"request": request,
                                       "project_version": db_dash(),
                                       "projects": projects or []})


@router.get("/{project_name}/versions/{project_version}/tickets",
            response_class=HTMLResponse,
            tags=["Front - Utils"],
            include_in_schema=False)
async def project_version_tickets(request: Request, project_name, project_version):

    return templates.TemplateResponse("ticket_view.html",
                                      {"request": request,
                                       "tickets": get_tickets(project_name, project_version),
                                       "project_name": project_name,
                                       "project_version": project_version})


@router.delete("/clear",
               response_class=HTMLResponse,
               tags=["Front - Utils"],
               include_in_schema=False)
async def return_void():
    return HTMLResponse("")


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
    return HTMLResponse("""<span _="on htmx:afterSettle wait 1s then then remove .modal-backdrop then remove .modal then wait 1s then go to url /"/> """)


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
    return templates.TemplateResponse("ticket_row_edit.html",
                                      {"request": request,
                                       "ticket": get_ticket(project_name,
                                                            project_version,
                                                            reference),
                                       "project_name": project_name,
                                       "project_version": project_version})


@router.get("/{project_name}/versions/{project_version}/tickets/{reference}",
            response_class=HTMLResponse,
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_ticket(request: Request, project_name, project_version, reference):
    return templates.TemplateResponse("ticket_row.html",
                                      {"request": request,
                                       "ticket": get_ticket(project_name,
                                                            project_version,
                                                            reference),
                                       "project_name": project_name,
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
        return templates.TemplateResponse("modal_error.html",
                                          {"request": request,
                                           "message": "You're not authorized",
                                           "my_fetch": f"then fetch /{project_name}/versions/"
                                                       f"{project_version}/tickets as html "
                                                       f"put the result into #tickets "})
    # TODO check if a refactor might enhance readability
    res = update_ticket(project_name,
                        project_version,
                        reference,
                        UpdatedTicket(description=body["description"], status=body["status"]))
    if not res.acknowledged:
        logging.getLogger().error("No done")
    background_task.add_task(update_values, project_name, project_version)
    return templates.TemplateResponse("ticket_row.html",
                                      {"request": request,
                                       "ticket": get_ticket(project_name,
                                                            project_version,
                                                            reference),
                                       "project_name": project_name,
                                       "project_version": project_version})


@router.get("/testResults",
            response_class=HTMLResponse,
            tags=["Front - Campaign"],
            include_in_schema=False)
async def get_test_results(request: Request):
    projects = registered_projects()
    result = {project: get_project_results(project) for project in projects}
    return templates.TemplateResponse("test_results.html",
                                      {"request": request,
                                       "results": result})
