# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Union

from fastapi import APIRouter, HTTPException, Security

from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import create_project_version
from app.database.postgre.pg_versions import get_version, update_version_data
from app.database.utils.object_existence import if_error_raise_http, project_version_exists, project_version_raise
from app.schema.bugs_schema import UpdateVersion
from app.schema.error_code import ApplicationError, ErrorMessage
from app.schema.project_schema import RegisterVersion, RegisterVersionResponse
from app.schema.users import UpdateUser
from app.schema.versions_schema import Version

router = APIRouter(
    prefix="/api/v1"
)


@router.post("/projects/{project_name}/versions",
             response_model=RegisterVersionResponse,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case)"},
                 400: {"model": ErrorMessage,
                       "description": "version already exist"}
             },
             tags=["Versions"],
             description="""Create a new version of this project
Only admin can create new version.""")
async def create_version(project_name: str,
                         project: RegisterVersion,
                         user: UpdateUser = Security(authorize_user,
                                                     scopes=["admin"])) -> RegisterVersionResponse | ApplicationError:
    await project_version_raise(project_name)

    try:
        result = await create_project_version(project_name, project)
    except Exception as exp:
        raise HTTPException(500, detail=" ".join(exp.args)) from exp

    return if_error_raise_http(result)


@router.get("/projects/{project_name}/versions/{version}",
            response_model=Version,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description="Retrieve a specific project's version details")
async def version_details(project_name: str,
                          version: str,
                          user: UpdateUser = Security(
                              authorize_user, scopes=["admin", "user"])
                          ) -> Version | ApplicationError:
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
                         user: UpdateUser = Security(
                             authorize_user,
                             scopes=["admin"])) -> Version | ApplicationError:
    await project_version_exists(project_name, version)
    try:
        result = await update_version_data(project_name.casefold(), version.casefold(), body)
    except Exception as exp:
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)
