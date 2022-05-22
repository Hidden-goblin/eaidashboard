# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Any, List, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, Query, Response, Security
from pymongo import MongoClient

from app.app_exception import (ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion)
from app.database.projects import create_project_version, get_project
from app.database.versions import get_version, update_version_data, update_version_status
from app.schema.project_schema import ErrorMessage, Project, RegisterVersion, UpdateVersion, Version
from app.conf import mongo_string

router = APIRouter(
    prefix="/api/v1"
)


@router.get("/projects",
            response_model=List[Project],
            tags=["Projects"])
async def projects(response: Response,
                   skip: int = 0,
                   limit: int = 100):
    client = MongoClient(mongo_string)
    db_names = client.list_database_names()
    db_names.pop(db_names.index("admin")) if 'admin' in db_names else None
    db_names.pop(db_names.index("config")) if 'config' in db_names else None
    db_names.pop(db_names.index("local")) if 'local' in db_names else None
    db_names.pop(db_names.index("settings")) if 'settings' in db_names else None

    db_names.sort()
    db_names = db_names[skip:limit]
    return [{"name": db_name,
             "current": client[db_name]["current"].count_documents({}),
             "future": client[db_name]["future"].count_documents({}),
             "archive": client[db_name]["archive"].count_documents({})}
            for db_name in db_names]


@router.post("/projects",
             response_model=str,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case)"},
                 400: {"model": ErrorMessage,
                       "description": "version already exist"}
             },
             tags=["Projects"])
async def post_projects(project: RegisterVersion):
    try:
        result = create_project_version(project)
        return str(result.inserted_id)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except DuplicateArchivedVersion as dav:
        raise HTTPException(400, detail=" ".join(dav.args)) from dav
    except DuplicateFutureVersion as dfv:
        raise HTTPException(400, detail=" ".join(dfv.args)) from dfv
    except DuplicateInProgressVersion as dipv:
        raise HTTPException(400, detail=" ".join(dipv.args)) from dipv


@router.get("/projects/{project_name}",
            response_model=Project,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Projects"]
            )
async def one_project(project_name: str,
                      sections: Union[List[str], None] = Query(default=None)):
    try:
        return get_project(project_name.casefold(), sections)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


@router.get("/projects/{project_name}/{version}",
            response_model=Union[Version, dict],
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"])
async def version_details(project_name: str, version: str):
    try:
        return get_version(project_name.casefold(), version.casefold())
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


@router.put("/projects/{project_name}/{version}",
            response_model=Version,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description=f"""Update the project-version on status, issues and bugs.
            
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
            """
            )
async def update_version(project_name: str, version: str, body: UpdateVersion):
    result = None
    if "status" in body:
        result = update_version_status(project_name, version, body["status"])
    # Check it's ok :/

    return update_version_data(project_name.casefold(), version.casefold(), body)
