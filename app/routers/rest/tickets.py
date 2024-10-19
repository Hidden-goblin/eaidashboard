# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from fastapi import APIRouter, HTTPException, Security
from psycopg import IntegrityError

from app.database.authorization import authorize_user
from app.database.postgre.pg_campaigns_management import enrich_tickets_with_campaigns
from app.database.postgre.pg_tickets import add_ticket, get_ticket, get_tickets, update_ticket
from app.database.utils.object_existence import if_error_raise_http, project_version_raise
from app.schema.error_code import ErrorMessage
from app.schema.project_schema import RegisterVersionResponse
from app.schema.ticket_schema import EnrichedTicket, Ticket, ToBeTicket, UpdatedTicket
from app.schema.users import UpdateUser
from app.utils.log_management import log_error

router = APIRouter(prefix="/api/v1")


@router.post(
    "/projects/{project_name}/versions/{version}/tickets/",
    responses={
        400: {"model": ErrorMessage, "description": "Ticket reference already exists for the project"},
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case)" " or version does not exist",
        },
        422: {"model": ErrorMessage, "description": "The payload does not match the expected schema"},
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
    tags=["Tickets"],
    description="Add one ticket to a version. Admin ou user can do so.",
)
async def create_ticket(
    project_name: str,
    version: str,
    ticket: ToBeTicket,
    user: UpdateUser = Security(authorize_user, scopes=["admin"]),
) -> RegisterVersionResponse:
    await project_version_raise(
        project_name,
        version,
    )
    try:
        result = await add_ticket(
            project_name,
            version,
            ticket,
        )
    except IntegrityError as ie:
        raise HTTPException(400, detail=" ".join(ie.args)) from ie
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception
    return if_error_raise_http(result)


@router.get(
    "/projects/{project_name}/versions/{version}/tickets/",
    response_model=List[EnrichedTicket],
    responses={
        400: {"model": ErrorMessage, "description": "Mal"},
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case)" " or version does not exist",
        },
        500: {"model": ErrorMessage, "description": "Backend computation error"},
    },
    tags=["Tickets"],
    description="Retrieve all tickets in a version",
)
async def router_get_tickets(
    project_name: str,
    version: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> List[EnrichedTicket]:
    await project_version_raise(
        project_name,
        version,
    )
    try:
        tickets = await get_tickets(
            project_name,
            version,
        )
        tickets = await enrich_tickets_with_campaigns(
            project_name,
            version,
            tickets,
        )
        return tickets
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception


@router.get(
    "/projects/{project_name}/versions/{version}/tickets/{reference}",
    response_model=Ticket,
    responses={
        500: {"model": ErrorMessage, "description": "Backend computation error"},
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case)"
            " or version does not exist"
            " or ticket does not exist for project-version",
        },
    },
    tags=["Tickets"],
    description="Retrieve one ticket of a version",
)
async def get_one_ticket(
    project_name: str,
    version: str,
    reference: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> Ticket:
    await project_version_raise(
        project_name,
        version,
    )

    try:
        result = await get_ticket(
            project_name,
            version,
            reference,
        )
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception

    return if_error_raise_http(result)


@router.put(
    "/projects/{project_name}/versions/{version}/tickets/{reference}",
    response_model=str,
    responses={
        401: {"model": ErrorMessage, "description": "You are not authorized to process this action"},
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case)" " or version does not exist",
        },
        422: {"model": ErrorMessage, "description": "The payload does not match the expected schema"},
        500: {"model": ErrorMessage, "description": "Backend computation error"},
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
""",
)
async def update_one_ticket(
    project_name: str,
    version: str,
    reference: str,
    ticket: UpdatedTicket,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> str:
    await project_version_raise(
        project_name,
        version,
    )
    try:
        res = await update_ticket(
            project_name,
            version,
            reference,
            ticket,
        )
    except Exception as exception:
        log_error(repr(exception))
        raise HTTPException(500, detail=" ".join(exception.args)) from exception

    return str(if_error_raise_http(res).inserted_id)
