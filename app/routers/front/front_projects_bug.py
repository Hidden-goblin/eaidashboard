# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter
from starlette.requests import Request

from app.conf import templates
from app.database.mongo.bugs import get_bugs
from app.database.settings import registered_projects
from app.schema.mongo_enums import BugStatusEnum

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/bugs",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_bugs(project_name: str,
                             request: Request,
                             status: Optional[str] = None):
    if status is not None:
        bugs = get_bugs(project_name)
    else:
        bugs = get_bugs(project_name, status=BugStatusEnum.open)
    projects = registered_projects()
    return templates.TemplateResponse("bugs.html",
                                      {
                                          "request": request,
                                          "bugs": bugs,
                                          "projects": projects,
                                          "display_closed": status,
                                          "project_name": project_name
                                      })
