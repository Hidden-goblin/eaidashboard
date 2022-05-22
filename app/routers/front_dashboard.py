# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.conf import templates
from app.database.versions import dashboard as db_dash
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html",
                                      {"request": request,
                                       "project_version": db_dash()})
