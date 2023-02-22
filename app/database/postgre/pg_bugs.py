# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.bugs_schema import BugTicket, UpdateBugTicket


async def compute_bugs(project_name):
    pass

async def get_bugs(project_name: str,
             status: Optional[BugStatusEnum] = None,
             criticality: Optional[BugCriticalityEnum] = None,
             version: str = None):
    pass

async def db_get_bug(project_name: str,
               internal_id: str) -> dict:
    return {}

async def db_update_bugs(project_name, internal_id, bug_ticket: UpdateBugTicket):
    pass

async def version_bugs(project_name, version, side_version=None):
    pass

async def insert_bug(project_name: str, bug_ticket: BugTicket):
    pass
