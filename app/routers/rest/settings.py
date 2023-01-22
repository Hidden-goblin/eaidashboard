# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List

from fastapi import APIRouter, HTTPException, Depends, Response, Security, BackgroundTasks
from pymongo import MongoClient

import app.database.mongo.projects
from app.app_exception import ProjectNameInvalid
from app.database.authorization import authorize_user
from app.schema.project_schema import (ErrorMessage, Project, RegisterProject)
from app.database.mongo.projects import (set_index, register_project)

router = APIRouter(
    prefix="/api/v1/settings"
)


@router.post("/projects",
             response_model=Project,
             tags=["Settings"],
             description="""Create a new project. \n project name must be strictly less than 64 
             characters""",
             responses={
                 400: {"model": ErrorMessage,
                       "description": "Project name is not a valid one. More than 63 characters or"
                                      " contains / \\ $ character"},
                 401: {"model": ErrorMessage,
                       "description": "You are not authenticated"},
                 500: {"model": ErrorMessage,
                       "description": "Error during server computing"}
             }
             )
async def post_register_projects(project: RegisterProject,
                                 background_task: BackgroundTasks,
                                 user: Any = Security(authorize_user, scopes=["admin"])):
    try:
        _project_name = await register_project(project.dict()["name"])
        background_task.add_task(set_index, _project_name)
        return {"name": _project_name}
    except ProjectNameInvalid as pni:
        raise HTTPException(400, detail=" ".join(pni.args)) from pni
    except Exception as exception:
        raise HTTPException(500, detail=" ".join(exception.args)) from exception


@router.get("/projects",
            response_model=List[str],
            tags=["Settings"],
            description="""Register a new project. Only admin can do so."""
            )
async def get_registered_projects():
    return await app.database.mongo.projects.registered_projects()
