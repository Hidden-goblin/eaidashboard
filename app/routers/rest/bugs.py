# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Security

from app.database.authorization import authorize_user

from app.database.postgre.pg_bugs import (
    db_update_bugs,
    get_bugs as db_g_bugs,
    insert_bug)

from app.schema.mongo_enums import (BugCriticalityEnum, BugStatusEnum)
from app.schema.project_schema import (ErrorMessage)
from app.schema.status_enum import TicketType
from app.schema.bugs_schema import BugTicket, BugTicketFull, UpdateBugTicket

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/bugs",
            tags=["Bug"],
            response_model=List[BugTicketFull]
            )
async def get_bugs(project_name: str,
                   status: Optional[TicketType] = None
                   ):
    try:
        return await db_g_bugs(project_name, status)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.get("/{project_name}/versions/{version}/bugs",
            tags=["Bug"],
            response_model=List[BugTicket],
            responses={
                404: {"model": ErrorMessage,
                      "description": "Version is not fount"}
            })
async def get_bugs_for_version(project_name: str,
                               version: str,
                               status: Optional[BugStatusEnum] = None,
                               criticality: Optional[BugCriticalityEnum] = None):
    try:
        return await db_g_bugs(project_name, status, criticality, version)
    except Exception as exp:
        raise HTTPException(500, repr(exp))

@router.post("/{project_name}/bugs",
             tags=["Bug"])
async def create_bugs(project_name: str,
                      bug: BugTicket,
                      user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        return await insert_bug(project_name, bug)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.put("/{project_name}/bugs/{bug_internal_id}",
            tags=["Bug"],
            response_model=BugTicket)
async def update_bugs(project_name: str,
                      bug_internal_id: str,
                      body: UpdateBugTicket,
                      user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        return await db_update_bugs(project_name, bug_internal_id, body)
    except Exception as exp:
        raise HTTPException(500, repr(exp))

