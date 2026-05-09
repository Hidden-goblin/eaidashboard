# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from typing import List, Union

from fastapi import APIRouter, HTTPException, Query, Response, Security

from app.database.authorization import authorize_user
from app.database.postgre.pg_campaigns_management import retrieve_campaigns
from app.database.postgre.projects.pg_projects import get_project, get_projects
from app.database.postgre.versions.pg_versions import dashboard, get_project_versions_v2
from app.database.utils.object_existence import project_version_raise
from app.schema.campaign_schema import CampaignProjections
from app.schema.dashboard_schema import Dashboard
from app.schema.error_code import ErrorMessage
from app.schema.project_enum import ProjectProjections
from app.schema.project_schema import DashboardProject, Project, TicketProject
from app.schema.users import UpdateUser
from app.schema.versions_schema import VersionProjections

router = APIRouter(prefix="/api/v1")
routerv2 = APIRouter(prefix="/api/v2")


@router.get(
    "/dashboard",
    description="""Summarize the projects' status on current testing.

**Please note**: the x-total-count in the header represents the total count of projects not the different
versions under test.
            """,
    tags=["Dashboard"],
    response_model=List[DashboardProject],
)
async def api_dashboard(
    response: Response,
    skip: int = 0,
    limit: int = 10,
) -> List[DashboardProject]:
    try:
        # TODO add total # of project in response header
        elements, count = await dashboard(
            skip,
            limit,
        )
        response.headers["X-total-count"] = str(count)
        return elements
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp


@routerv2.get(
    "/dashboard",
    description="""Summarize the projects' status on current testing.

**Please note**: the x-total-count in the header represents the total count of projects not the different
versions under test.
            """,
    tags=["Dashboard"],
    response_model=Dashboard,
)
async def api_dashboard_v2(
    response: Response,
    skip: int = 0,
    limit: int = 10,
) -> Dashboard:
    try:
        # TODO add total # of project in response header
        elements, count = await dashboard(
            skip,
            limit,
        )
        response.headers["X-total-count"] = str(count)
        return Dashboard(projects=elements)
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp


@router.get(
    "/projects",
    response_model=List[Project],
    tags=["Projects"],
    description="Retrieve all projects",
)
async def projects(
    response: Response,
    skip: int = 0,
    limit: int = 100,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> List[Project]:
    try:
        elements, count = await get_projects(skip, limit)
        response.headers["X-total-count"] = str(count)
        return elements
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args))


@router.get(
    "/projects/{project_name}",
    response_model=TicketProject,
    responses={404: {"model": ErrorMessage, "description": "Project name is not registered (ignore case)"}},
    tags=["Projects"],
    description="""Retrieve one specific project details.

**sections** has value in

  - future
  - archived
  - current

denoting the project's version you want to retrieve.
            """,
)
async def one_project(
    project_name: str,
    sections: Union[List[str], None] = Query(default=None),
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> TicketProject:
    await project_version_raise(project_name)
    try:
        return await get_project(project_name.casefold(), sections)
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp


@routerv2.get(
    "/projects/{project_name}",
    response_model=Union[CampaignProjections, VersionProjections],
    responses={404: {"model": ErrorMessage, "description": "Project name is not registered (ignore case)"}},
    tags=["Projects"],
    description="""Retrieve a projection of the projects.

    Projects contain several aspect. Here, you retrieve one of the aspect - versions or campaigns.
    """,
)
async def project(
    project_name: str,
    projection: ProjectProjections = ProjectProjections.VERSIONS,
    limit: int = 10,
    skip: int = 0,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> CampaignProjections | VersionProjections:
    await project_version_raise(project_name)
    try:
        _options = {
            ProjectProjections.VERSIONS: get_project_versions_v2,
            ProjectProjections.FUTURE_VERSIONS: get_project_versions_v2,
            ProjectProjections.ARCHIVED_VERSIONS: get_project_versions_v2,
            ProjectProjections.CAMPAIGNS: retrieve_campaigns,
            ProjectProjections.ARCHIVED_CAMPAIGNS: retrieve_campaigns,
        }

        return await _options[projection](project_name, projection, limit, skip)
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp
