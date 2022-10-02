# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException, Depends, Response, Security, BackgroundTasks
from pymongo import MongoClient

from app.database import settings
from app.database.authorization import authorize_user
from app.schema.project_schema import Project, RegisterProject
from app.database.settings import set_index

router = APIRouter(
    prefix="/api/v1/settings"
)


@router.post("/projects",
             response_model=Project,
             tags=["Settings"])
async def post_register_projets(project: RegisterProject,
                                background_task: BackgroundTasks,
                                user: Any = Security(authorize_user, scopes=["admin"])):
    _project_name = settings.register_project(project.dict()["name"])
    background_task.add_task(set_index, _project_name)
    return {"name": _project_name}


@router.get("/projects",
            response_model=List[str],
            tags=["Settings"],
            description="""Register a new project. Only admin can do so."""
            )
async def get_registered_projects():
    return settings.registered_projects()
