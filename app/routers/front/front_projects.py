# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
import urllib.parse

from fastapi import APIRouter, Form, HTTPException
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.conf import templates
from app.database.authentication import authenticate_user, create_access_token, invalidate_token
from app.database.authorization import is_updatable
from app.database.projects import create_project_version, get_project, get_project_results
from app.database.settings import registered_projects
from app.database.testrepository import db_project_epics, db_project_features
from app.database.tickets import get_ticket, get_tickets, update_ticket, update_values
from app.database.versions import dashboard as db_dash
from app.schema.project_schema import RegisterVersion, UpdatedTicket

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_management(project_name: str,
                                   request: Request):
    _versions = get_project(project_name, None)
    versions = [{"value": item["version"], "status": item["status"]} for item in _versions["future"]]
    versions.extend(
        [{"value": item["version"], "status": item["status"]} for item in _versions["current"]])
    versions.extend(
        [{"value": item["version"], "status": item["status"]} for item in _versions["archived"]])
    return templates.TemplateResponse("project.html",
                                      {
                                          "request": request,
                                          "versions": versions,
                                          "project_name": project_name
                                      })


@router.get("/{project_name}/versions",
            tags=["Front - Project"],
            include_in_schema=False)
async def project_versions(project_name: str,
                           request: Request):
    _versions = get_project(project_name, None)
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
                                          "project_name": project_name
                                      })


@router.get("/{project_name}/forms/version",
            tags=["Front - Project"],
            include_in_schema=False)
async def form_version(project_name: str,
                       request: Request):
    return templates.TemplateResponse("forms/add_version.html",
                                      {
                                          "request": request,
                                          "project_name": project_name
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
    create_project_version(project_name, RegisterVersion(version=version))
    return HTMLResponse("")


async def repository_dropdowns(project_name: str, request: Request, epic: str, feature: str):
    if epic is None and feature is None:
        epics = db_project_epics(project_name)
        features = {feature["name"] for feature in db_project_features(project_name, epics[0])}
        return templates.TemplateResponse("selectors/epic_label_selectors.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "epics": epics,
                                              "features": features
                                          })
    if epic is not None and feature is None:
        features = {feature["name"] for feature in db_project_features(project_name, epic)}
        return templates.TemplateResponse("selectors/feature_label_selectors.html",
                                          {
                                              "request": request,
                                              "project_name": project_name,
                                              "features": features
                                          })


async def repository_board(project_name, request, epic, feature, limit, skip):

    pass
