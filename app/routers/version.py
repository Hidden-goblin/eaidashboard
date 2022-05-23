# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, Query, Response, Security
from pymongo import MongoClient

from app.app_exception import (IncorrectTicketCount, ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion)
from app.database.db_settings import DashCollection
from app.database.projects import create_project_version, get_project
from app.database.versions import get_version, move_tickets, update_version_data, \
    update_version_status
from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       Tickets, TicketType, UpdateVersion,
                                       Version,
                                       TicketProject)
from app.conf import mongo_string

router = APIRouter(
    prefix="/api/v1"
)


@router.put("/projects/{project_name}/{version}/tickets/{ticket_type}",
            response_model=Version,
            responses={
                400: {"model": ErrorMessage,
                      "description": "Where move is not correct"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description="Move one ticket type to other ticket types. All value are positive"
            )
async def put_tickets(project_name: str,
                      version: str,
                      ticket_type: TicketType,
                      ticket_dispatch: Tickets):
    try:
        return move_tickets(project_name, version, ticket_type, ticket_dispatch)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except IncorrectTicketCount as itc:
        raise HTTPException(400, detail=" ".join(itc.args)) from itc
