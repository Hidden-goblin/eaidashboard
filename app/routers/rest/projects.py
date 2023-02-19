# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from io import StringIO
from typing import Any, List, Union

from fastapi import (APIRouter,
                     File,
                     HTTPException,
                     Query,
                     Response,
                     Security,
                     UploadFile)
from csv import DictReader

from app import conf
from app.app_exception import (ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion)
from app.database.authorization import authorize_user

if conf.MIGRATION_DONE:
    from app.database.postgre.pg_projects import (create_project_version,
                                                  get_project,
                                                  get_projects)
    from app.database.postgre.pg_versions import (get_version,
                                                  update_version_data,
                                                  update_version_status)
else:
    from app.database.mongo.projects import (create_project_version, get_project,
        get_projects)
    from app.database.mongo.versions import get_version, update_version_data, update_version_status

from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       UpdateVersion,
                                       Version,
                                       TicketProject)

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

    return await get_projects(skip, limit)


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
    try:
        return await get_project(project_name.casefold(), sections)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


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
    try:
        result = await create_project_version(project_name,project)
        return str(result.inserted_id)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except DuplicateArchivedVersion as dav:
        raise HTTPException(400, detail=" ".join(dav.args)) from dav
    except DuplicateFutureVersion as dfv:
        raise HTTPException(400, detail=" ".join(dfv.args)) from dfv
    except DuplicateInProgressVersion as dipv:
        raise HTTPException(400, detail=" ".join(dipv.args)) from dipv


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
    try:
        return await get_version(project_name.casefold(), version.casefold())
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


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

   - in progress
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
    result = None
    if "status" in body.dict() and body.dict()["status"] is not None:
        result = await update_version_status(project_name, version, body.dict()["status"])
    # Check it's ok :/

    return await update_version_data(project_name.casefold(), version.casefold(), body)


# @router.post("/projects/{project_name}/results")
# async def upload_results(project_name: str,
#                          result_date: str,
#                          file: UploadFile = File(),
#                          user: Any = Security(authorize_user, scopes=["admin", "user"])
#                          ):
#     contents = await file.read()
#     decoded = contents.decode()
#     buffer = StringIO(decoded)
#     rows = DictReader(buffer)
#     results = [{**row, "date": datetime.strptime(result_date, "%Y%m%dT%H:%M")} for row in rows]
#     await insert_results(project_name, results)
#     return {"result": "ok"}


# @router.get("/projects/{project_name}/results")
# async def get_results(project_name: str):
#     return await get_project_results(project_name)


