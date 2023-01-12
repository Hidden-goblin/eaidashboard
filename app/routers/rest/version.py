# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List

from fastapi import APIRouter, HTTPException, Security
from pymongo.errors import DuplicateKeyError
from starlette.background import BackgroundTasks

from app.app_exception import (IncorrectTicketCount, VersionNotFound)
from app.database.authorization import authorize_user
from app.database.mongo.tickets import add_ticket, get_ticket, get_tickets, update_ticket, update_values

from app.database.postgre.pg_campaigns_management import enrich_tickets_with_campaigns
from app.schema.project_schema import (ErrorMessage)
from app.schema.ticket_schema import EnrichedTicket, Ticket, ToBeTicket, UpdatedTicket

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
             description="Add one ticket to a version. Admin ou user can do so."
                         "Update the project statistics as background task."
             )
async def create_ticket(project_name: str,
                        version: str,
                        ticket: ToBeTicket,
                        background_task: BackgroundTasks,
                        user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        result = await add_ticket(project_name, version, ticket)
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
            response_model=List[EnrichedTicket],
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
        tickets = await get_tickets(project_name, version)
        tickets = await enrich_tickets_with_campaigns(project_name, version, tickets)
        return tickets
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
    try:
        return await get_ticket(project_name, version, reference)
    except VersionNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except Exception as exception:
        raise HTTPException(400, detail=" ".join(exception.args)) from exception


@router.put("/projects/{project_name}/versions/{version}/tickets/{reference}",
            response_model=str,
            responses={
                400: {"model": ErrorMessage,
                      "description": "Mal"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"}
            },
            tags=["Tickets"],
            description="""Update one ticket of a version
            
**status** is one of:

    - open
    - cancelled
    - blocked
    - in_progress
    - done
            
Only admin or user can update.
            
Update version statistics as a background task""")
async def update_one_ticket(project_name: str,
                            version: str,
                            reference: str,
                            ticket: UpdatedTicket,
                            background_task: BackgroundTasks,
                            user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        res = await update_ticket(project_name, version, reference, ticket)
        if not res.acknowledged:
            raise Exception("update not made")
        background_task.add_task(update_values, project_name, version)
        if "version" in ticket.dict() and ticket.dict()["version"] is not None:
            background_task.add_task(update_values, project_name, ticket.dict()["version"])
        return str(res.inserted_id)
    except VersionNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except Exception as exception:
        raise HTTPException(400, detail=" ".join(exception.args)) from exception
