# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.conf import templates
from app.database.tickets import get_tickets
from app.database.versions import dashboard as db_dash
router = APIRouter()


@router.get("/", response_class=HTMLResponse,
            tags=["Front"])
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html",
                                      {"request": request,
                                       "project_version": db_dash()})


@router.get("/{project_name}/versions/{project_version}/tickets",
            response_class=HTMLResponse,
            tags=["Front"])
async def project_version_tickets(request: Request, project_name, project_version):

    return templates.TemplateResponse("ticket_view.html",
                                      {"request": request,
                                       "tickets": get_tickets(project_name, project_version)})


@router.delete("/clear",
               tags=["Front"])
async def return_void():
    return HTMLResponse("")
