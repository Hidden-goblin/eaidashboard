# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Security
from starlette.background import BackgroundTasks

from app.database.authorization import authorize_user
from app.database.mongo.bugs import (compute_bugs, db_update_bugs, get_bugs as db_g_bugs,
                                     insert_bug, version_bugs)
from app.database.mongo.versions import get_version_and_collection
from app.schema.mongo_enums import (BugCriticalityEnum, BugStatusEnum)
from app.schema.project_schema import (BugTicket, BugTicketResponse, ErrorMessage, TicketType,
                                       UpdateBugTicket)

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/bugs",
            tags=["Bug"],
            response_model=List[BugTicketResponse]
            )
async def get_bugs(project_name: str,
                   background_task: BackgroundTasks,
                   status: Optional[TicketType] = None
                   ):

    background_task.add_task(compute_bugs, project_name)
    return await db_g_bugs(project_name, status)


@router.get("/{project_name}/versions/{version}/bugs",
            tags=["Bug"],
            response_model=List[BugTicket],
            responses={
                404: {"model": ErrorMessage,
                      "description": "Version is not fount"}
            })
async def get_bugs_for_version(project_name: str,
                               version: str,
                               background_task: BackgroundTasks,
                               status: Optional[BugStatusEnum] = None,
                               criticality: Optional[BugCriticalityEnum] = None):
    _version, __ = await get_version_and_collection(project_name, version)
    if not _version:
        raise HTTPException(404,
                            detail=f"Version {version} is not found for project {project_name}")
    background_task.add_task(version_bugs, project_name, version)
    return await db_g_bugs(project_name, status, criticality, version)


@router.post("/{project_name}/bugs",
             tags=["Bug"])
async def create_bugs(project_name: str,
                      bug: BugTicket,
                      background_task: BackgroundTasks,
                      user: Any = Security(authorize_user, scopes=["admin", "user"])):
    res = await insert_bug(project_name, bug)
    background_task.add_task(version_bugs, project_name, bug.version)
    return res


@router.put("/{project_name}/bugs/{bug_internal_id}",
            tags=["Bug"],
            response_model=BugTicket)
async def update_bugs(project_name: str,
                      bug_internal_id: str,
                      body: UpdateBugTicket,
                      background_task: BackgroundTasks,
                      user: Any = Security(authorize_user, scopes=["admin", "user"])):
    background_task.add_task(version_bugs, project_name, "")
    return await db_update_bugs(project_name, bug_internal_id, body)

