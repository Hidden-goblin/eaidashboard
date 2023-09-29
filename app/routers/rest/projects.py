# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from typing import List, Union

from fastapi import APIRouter, HTTPException, Query, Response, Security

from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import get_project, get_projects
from app.database.postgre.pg_versions import dashboard
from app.database.utils.object_existence import project_version_raise
from app.schema.error_code import ErrorMessage
from app.schema.project_schema import Dashboard, Project, TicketProject
from app.schema.users import UpdateUser

router = APIRouter(
    prefix="/api/v1"
)


@router.get("/dashboard",
            description="""Summarize the projects' status on current testing.

**Please note**: the x-total-count in the header represents the total count of projects not the different
versions under test.
            """,
            tags=["Dashboard"],
            response_model=List[Dashboard])
async def api_dashboard(response: Response,
                        skip: int = 0,
                        limit: int = 10
                        ) -> List[Dashboard]:
    try:
        # TODO add total # of project in response header
        elements, count = await dashboard(skip, limit)
        response.headers["X-total-count"] = str(count)
        return elements
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp


@router.get("/projects",
            response_model=List[Project],
            tags=["Projects"],
            description="Retrieve all projects")
async def projects(response: Response,
                   skip: int = 0,
                   limit: int = 100,
                   user: UpdateUser = Security(
                       authorize_user, scopes=["admin", "user"])

                   ) -> List[Project]:
    try:
        # TODO add total # of project in response header
        elements, count = await get_projects(skip, limit)
        response.headers["X-total-count"] = str(count)
        return elements
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp


@router.get("/projects/{project_name}",
            response_model=TicketProject,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Projects"],
            description="""Retrieve one specific project details.

**sections** has value in

  - future
  - archived
  - current

denoting the project's version you want to retrieve.
            """
            )
async def one_project(project_name: str,
                      sections: Union[List[str], None] = Query(default=None),
                      user: UpdateUser = Security(
                          authorize_user, scopes=["admin", "user"])
                      ) -> TicketProject:
    await project_version_raise(project_name)
    try:
        return await get_project(project_name.casefold(), sections)
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp
