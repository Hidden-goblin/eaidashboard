# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from typing import Any, List, Union

from fastapi import APIRouter, HTTPException, Query, Response, Security

from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import create_project_version, get_project, get_projects
from app.database.postgre.pg_versions import get_version, update_version_data
from app.database.utils.object_existence import if_error_raise_http, project_version_exists, project_version_raise
from app.schema.bugs_schema import UpdateVersion
from app.schema.project_schema import ErrorMessage, Project, RegisterVersion, TicketProject
from app.schema.versions_schema import Version

router = APIRouter(
    prefix="/api/v1"
)


@router.get("/projects",
            response_model=List[Project],
            tags=["Projects"],
            description="Retrieve all projects")
async def projects(response: Response,
                   skip: int = 0,
                   limit: int = 100):
    try:
        # TODO add total # of project in response header
        return await get_projects(skip, limit)
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
                      sections: Union[List[str], None] = Query(default=None)):
    await project_version_raise(project_name)
    try:
        return await get_project(project_name.casefold(), sections)
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp


@router.post("/projects/{project_name}/versions",
             response_model=str,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case)"},
                 400: {"model": ErrorMessage,
                       "description": "version already exist"}
             },
             tags=["Projects"],
             description="""Create a new version of this project
Only admin can create new version.""")
async def post_projects(project_name: str,
                        project: RegisterVersion,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    await project_version_raise(project_name)

    try:
        result = await create_project_version(project_name, project)
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp

    return if_error_raise_http(result).inserted_id


@router.get("/projects/{project_name}/versions/{version}",
            response_model=Union[Version, dict],
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description="Retrieve a specific project's version details")
async def version_details(project_name: str,
                          version: str):
    await project_version_raise(project_name, version)

    try:
        result = await get_version(project_name.casefold(), version.casefold())
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp

    return if_error_raise_http(result)


@router.put("/projects/{project_name}/versions/{version}",
            response_model=Version,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description="""Update the project-version on status, issues and bugs.

**started** and **end_forecast** are dates in YYY-mm-dd format.

**status** is one of:

   - recorded
   - campaign started
   - campaign ended
   - test plan writing
   - test plan sent
   - test plan accepted
   - ter writing
   - ter sent
   - cancelled
   - archived

Only admin or user can update a version"""
            )
async def update_version(project_name: str,
                         version: str,
                         body: UpdateVersion,
                         user: Any = Security(authorize_user, scopes=["admin", "user"])):
    await project_version_exists(project_name, version)
    try:
        result = await update_version_data(project_name.casefold(), version.casefold(), body)
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)
