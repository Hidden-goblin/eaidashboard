# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter
from starlette.requests import Request

from app.conf import templates
from app.database.mongo.bugs import get_bugs
from app.database.postgre.testrepository import db_project_scenarios
from app.database.settings import registered_projects
from app.routers.front.front_projects import repository_dropdowns
from app.schema.mongo_enums import BugStatusEnum
from app.utils.pages import page_numbering

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/repository",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_repository(project_name: str,
                                   request: Request,
                                   status: Optional[str] = None):
    if status is not None:
        bugs = get_bugs(project_name)
    else:
        bugs = get_bugs(project_name, status=BugStatusEnum.open)
    projects = registered_projects()
    return templates.TemplateResponse("repository_board.html",
                                      {
                                          "request": request,
                                          "projects": projects,
                                          "repository": {}, # repository_board(project_name, request,                                                                         epic, feature),
                                          "display_closed": status,
                                          "project_name": project_name
                                      })


@router.get("/{project_name}/repository/epics-features",
            tags=["Front - Repository"],
            include_in_schema=False)
async def get_repository(project_name: str,
                         request: Request,
                         epic: str = None,
                         feature: str = None):

    return await repository_dropdowns(project_name, request, epic, feature)


@router.get("/{project_name}/repository/scenarios",
            tags=["Front - Repository"],
            include_in_schema=False)
async def get_scenario(project_name: str,
                       request: Request,
                       limit: int,
                       skip: int,
                       epic: Optional[str] = None,
                       feature: Optional[str] = None):
    scenarios, count = db_project_scenarios(project_name, epic, feature, limit=limit, offset=skip)
    pages, current_page = page_numbering(count, limit=limit, skip=skip)
    _filter = f"&epic={epic}&feature={feature}" if epic is not None and feature is not None else ""
    return templates.TemplateResponse("tables/scenario_table.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "scenarios": scenarios,
                                          "pages": pages,
                                          "current_page": current_page,
                                          "nav_bar": count > limit,
                                          "filter": _filter
                                      })


@router.post("/{project_name}/repository/scenarios",
             tags=["Front - Repository"],
             include_in_schema=False
             )
async def filter_repository(project_name: str,
                            body: dict,
                            request: Request):
    scenarios, count = db_project_scenarios(project_name, body["epic"], body["feature"], limit=10)
    pages, current_page = page_numbering(count, limit=10, skip=0)
    return templates.TemplateResponse("tables/scenario_table.html",
                                      {
                                          "request": request,
                                          "scenarios": scenarios,
                                          "pages": pages,
                                          "current_page": current_page,
                                          "nav_bar": count > 10,
                                          "filter": f"&epic={body['epic']}&feature={body['feature']}"
                                      })

