# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, Query, Response, Security
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, InvalidOperation
from starlette.background import BackgroundTasks

from app.app_exception import (IncorrectTicketCount, ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion, VersionNotFound)
from app.database.authorization import authorize_user
from app.database.db_settings import DashCollection
from app.database.projects import create_project_version, get_project
from app.database.tickets import add_ticket, get_tickets, update_values
from app.database.versions import get_version, move_tickets, update_version_data, \
    update_version_status
from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       Ticket, TicketType, ToBeTicket, UpdateVersion,
                                       Version,
                                       TicketProject)
from app.conf import mongo_string

router = APIRouter(
    prefix="/api/v1"
)


# @router.put("/projects/{project_name}/{version}/tickets/{ticket_type}",
#             response_model=Version,
#             responses={
#                 400: {"model": ErrorMessage,
#                       "description": "Where move is not correct"},
#                 404: {"model": ErrorMessage,
#                       "description": "Project name is not registered (ignore case)"}
#             },
#             tags=["Versions"],
#             description="Move one ticket type to other ticket types. All value are positive"
#             )
# async def put_tickets(project_name: str,
#                       version: str,
#                       ticket_type: TicketType,
#                       ticket_dispatch: Ticket,
#                       user: Any = Security(authorize_user, scopes=["admin", "user"])):
#     try:
#         return move_tickets(project_name, version, ticket_type, ticket_dispatch)
#     except ProjectNotRegistered as pnr:
#         raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
#     except IncorrectTicketCount as itc:
#         raise HTTPException(400, detail=" ".join(itc.args)) from itc


@router.post("/projects/{project_name}/versions/{version}/tickets/",
             responses={
                 400: {"model": ErrorMessage,
                       "description": "Mal"},
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case)"
                                      " or version does not exist"}
             },
             tags=["Tickets"],
             description="Add one ticket to a version"
             )
async def create_ticket(project_name: str,
                        version: str,
                        ticket: ToBeTicket,
                        background_task: BackgroundTasks,
                        user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        result = add_ticket(project_name, version, ticket)
        background_task.add_task(update_values, project_name, version)
        return str(result.inserted_id)
    except DuplicateKeyError as invalid:
        raise HTTPException(400, detail=" ".join(invalid.args)) from invalid
    except VersionNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except IncorrectTicketCount as itc:
        raise HTTPException(400, detail=" ".join(itc.args)) from itc
    except Exception as exception:
        raise HTTPException(400, detail=" ".join(exception.args)) from exception


@router.get("/projects/{project_name}/versions/{version}/tickets/",
            response_model=List[Ticket],
            responses={
                400: {"model": ErrorMessage,
                      "description": "Mal"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"}
            },
            tags=["Tickets"],
            description="Retrieve all tickets in a version")
async def router_get_tickets(project_name, version):
    try:
        return get_tickets(project_name, version)
    except VersionNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except Exception as exception:
        raise HTTPException(400, detail=" ".join(exception.args)) from exception


@router.get("/projects/{project_name}/versions/{version}/tickets/{reference}",
            response_model=Ticket,
            responses={
                400: {"model": ErrorMessage,
                      "description": "Mal"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"}
            },
            tags=["Tickets"],
            description="Retrieve one ticket of a version")
async def get_one_ticket(project_name: str, version: str, reference: str):
    pass


@router.put("/projects/{project_name}/versions/{version}/tickets/{reference}",
            response_model=Ticket,
            responses={
                400: {"model": ErrorMessage,
                      "description": "Mal"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"}
            },
            tags=["Tickets"],
            description="Update one ticket of a version")
async def update_one_ticket(project_name: str, version: str, reference: str):
    pass
