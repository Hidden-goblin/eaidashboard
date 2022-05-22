# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException, Depends, Response, Security, BackgroundTasks
from pymongo import MongoClient

from app.database import settings
from app.schema.project_schema import Project
from app.database.settings import set_index

router = APIRouter(
    prefix="/api/v1/settings"
)


@router.post("/projects",
             response_model=Project,
             tags=["Settings"])
async def post_register_projets(project: dict, background_task: BackgroundTasks):
    _project_name = settings.register_project(project["name"])
    background_task.add_task(set_index, _project_name)
    return {"name": _project_name}


@router.get("/projects",
            response_model=List[str],
            tags=["Settings"]
            )
async def get_registered_projects():
    return settings.registered_projects()
