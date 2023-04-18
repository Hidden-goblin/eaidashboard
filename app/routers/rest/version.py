# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List

from fastapi import APIRouter, HTTPException, Security
from psycopg import IntegrityError

from app.app_exception import (ProjectNotRegistered, TicketNotFound, UpdateException,
                               VersionNotFound)
from app.database.authorization import authorize_user
from app.database.postgre.pg_campaigns_management import enrich_tickets_with_campaigns
from app.database.postgre.pg_tickets import (add_ticket,
                                             get_ticket,
                                             get_tickets,
                                             update_ticket)
from app.database.utils.object_existence import project_version_exists
from app.schema.project_schema import (ErrorMessage)
from app.schema.ticket_schema import EnrichedTicket, Ticket, ToBeTicket, UpdatedTicket
from app.utils.log_management import log_error

router = APIRouter(
    prefix="/api/v1"
)


@router.post("/projects/{project_name}/versions/{version}/tickets/",
             responses={
                 400: {"model": ErrorMessage,
                       "description": "Ticket reference already exists for the project"},
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case)"
                                      " or version does not exist"},
                 422: {"model": ErrorMessage,
                       "description": "The payload does not match the expected schema"},
                 500: {"model": ErrorMessage,
                       "description": "Backend computation error"}
             },
             tags=["Tickets"],
             description="Add one ticket to a version. Admin ou user can do so."
                         )
async def create_ticket(project_name: str,
                        version: str,
                        ticket: ToBeTicket,
                        user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        result = await add_ticket(project_name, version, ticket)
        return str(result.inserted_id)
    except ProjectNotRegistered as pnr:
        log_error(repr(pnr))
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except VersionNotFound as vnf:
        log_error(repr(vnf))
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf
    except IntegrityError as ie:
        raise HTTPException(400, detail=" ".join(ie.args)) from ie
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception


@router.get("/projects/{project_name}/versions/{version}/tickets/",
            response_model=List[EnrichedTicket],
            responses={
                400: {"model": ErrorMessage,
                      "description": "Mal"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"},
                500: {"model": ErrorMessage,
                      "description": "Backend computation error"}
            },
            tags=["Tickets"],
            description="Retrieve all tickets in a version")
async def router_get_tickets(project_name, version):
    try:
        await project_version_exists(project_name, version)
        tickets = await get_tickets(project_name, version)
        tickets = await enrich_tickets_with_campaigns(project_name, version, tickets)
        return tickets
    except ProjectNotRegistered as pnr:
        log_error(repr(pnr))
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except VersionNotFound as vnf:
        log_error(repr(vnf))
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception


@router.get("/projects/{project_name}/versions/{version}/tickets/{reference}",
            response_model=Ticket,
            responses={
                500: {"model": ErrorMessage,
                      "description": "Backend computation error"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"
                                     " or ticket does not exist for project-version"}
            },
            tags=["Tickets"],
            description="Retrieve one ticket of a version")
async def get_one_ticket(project_name: str, version: str, reference: str):
    try:
        await project_version_exists(project_name, version)
        return await get_ticket(project_name, version, reference)
    except ProjectNotRegistered as pnr:
        log_error(repr(pnr))
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except VersionNotFound as pnr:
        log_error(repr(pnr))
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except TicketNotFound as tnf:
        log_error(repr(tnf))
        raise HTTPException(404, detail=" ".join(tnf.args)) from tnf
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception


@router.put("/projects/{project_name}/versions/{version}/tickets/{reference}",
            response_model=str,
            responses={
                401: {"model": ErrorMessage,
                      "description": "You are not authorized to process this action"},
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"
                                     " or version does not exist"},
                422: {"model": ErrorMessage,
                      "description": "The payload does not match the expected schema"},
                500: {"model": ErrorMessage,
                      "description": "Backend computation error"}
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
                            user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        await project_version_exists(project_name, version)
        res = await update_ticket(project_name, version, reference, ticket)
        return str(res.inserted_id)
    except ProjectNotRegistered as pnr:
        log_error(repr(pnr))
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except VersionNotFound as pnr:
        log_error(repr(pnr))
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except TicketNotFound as tnf:
        log_error(repr(tnf))
        raise HTTPException(404, detail=" ".join(tnf.args)) from tnf
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception
