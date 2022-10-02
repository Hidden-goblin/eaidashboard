# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter
from starlette.background import BackgroundTasks

from app.database.bugs import get_bugs as db_g_bugs, insert_bug, version_bugs
from app.schema.project_schema import BugTicket, TicketType

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/bugs")
async def get_bugs(project_name: str,
                   background_task: BackgroundTasks,
                   status: Optional[TicketType] = None
                   ):
    background_task.add_task(version_bugs, project_name, "1.0.0")
    return db_g_bugs(project_name, status)


@router.post("/{project_name}/bugs")
async def create_bugs(project_name: str,
                      bug: BugTicket):
    return insert_bug(project_name, bug)
