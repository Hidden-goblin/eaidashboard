# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter, HTTPException
from starlette.background import BackgroundTasks

from app.database.bugs import compute_bugs, get_bugs as db_g_bugs, insert_bug, version_bugs
from app.database.versions import get_version_and_collection
from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.project_schema import BugTicket, TicketType

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/bugs",
            tags=["Bug"])
async def get_bugs(project_name: str,
                   background_task: BackgroundTasks,
                   status: Optional[TicketType] = None
                   ):

    background_task.add_task(compute_bugs, project_name)
    return db_g_bugs(project_name, status)


@router.get("/{project_name}/bugs/{version}",
            tags=["Bug"])
async def get_bugs_for_version(project_name: str,
                               version: str,
                               background_task: BackgroundTasks,
                               status: Optional[BugStatusEnum] = None,
                               criticality: Optional[BugCriticalityEnum] = None):
    _version, __ = get_version_and_collection(project_name, version)
    if not _version:
        raise HTTPException(404,
                            detail=f"Version {version} is not found for project {project_name}")
    background_task.add_task(version_bugs, project_name, version)
    return db_g_bugs(project_name, status, criticality, version)


@router.post("/{project_name}/bugs",
             tags=["Bug"])
async def create_bugs(project_name: str,
                      bug: BugTicket,
                      background_task: BackgroundTasks):
    res = insert_bug(project_name, bug)
    background_task.add_task(version_bugs, project_name, bug.version)
    return res


@router.put("/{project_name}/bugs",
            tags=["Bug"])
async def update_bugs(project_name: str,
                      background_task: BackgroundTasks):
    background_task.add_task(version_bugs, project_name, "")

