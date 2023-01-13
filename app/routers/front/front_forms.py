# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter, Form, HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.conf import templates
from app.database.authorization import is_updatable
from app.database.mongo.projects import create_project_version, get_project
from app.database.postgre.testrepository import db_project_epics, db_project_features
from app.database.settings import registered_projects
from app.schema.project_schema import RegisterVersion

router = APIRouter(prefix="/front/v1/forms")


@router.get("/importRepository",
            tags=["Front - Repository"],
            include_in_schema=False)
async def get_import_repository_form(request: Request):
    if is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("forms/import_repository_from_csv.html",
                                          {"request": request,
                                           "project_name": request.headers.get("HX-PROJECT")})
    else:
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
