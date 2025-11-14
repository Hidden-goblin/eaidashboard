# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter, HTTPException, Security

from app.database.authorization import authorize_user
from app.database.utils.object_existence import project_version_raise
from app.database.utils.transitions import (
    authorized_transition,
    bug_authorized_transition,
    ticket_authorized_transition,
)
from app.schema.base_schema import GenericListModel
from app.schema.error_code import ErrorMessage
from app.schema.postgres_enums import CampaignStatusEnum
from app.schema.status_enum import BugStatusEnum, StatusEnum, TicketType
from app.schema.users import UpdateUser

router = APIRouter(prefix="/api/v1/settings/projects/{project_name}")


@router.get(
    "/workflow/{state}",
    response_model=GenericListModel,
    tags=["Settings"],
    description="""Retrieve the next states for a project-version""",
    responses={
        400: {
            "model": ErrorMessage,
            "description": "Project name is not a valid one. More than 63 characters or contains / \\ $ character",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        500: {"model": ErrorMessage, "description": "Error during server computing"},
    },
)
async def provide_next_states(
    project_name: str,
    state: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> GenericListModel:
    await project_version_raise(
        project_name,
    )
    try:
        if StatusEnum(state) not in authorized_transition:
            raise ValueError(f"'{state}' is not a valid project state.")
        else:
            return GenericListModel(data=authorized_transition[StatusEnum(state)])
    except ValueError as ve:
        raise HTTPException(400, detail=" ".join(ve.args)) from ve


@router.get(
    "/bugs/{state}",
    response_model=GenericListModel,
    tags=["Settings"],
    description="""Retrieve the bug next states for a project""",
    responses={
        400: {
            "model": ErrorMessage,
            "description": "Project name is not a valid one. More than 63 characters or contains / \\ $ character",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        500: {"model": ErrorMessage, "description": "Error during server computing"},
    },
)
async def provide_next_bug_states(
    project_name: str,
    state: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> GenericListModel:
    await project_version_raise(
        project_name,
    )
    try:
        if BugStatusEnum(state) not in bug_authorized_transition:
            raise ValueError(f"'{state}' is not a valid project state.")
        else:
            return GenericListModel(data=bug_authorized_transition[BugStatusEnum(state)])
    except ValueError as ve:
        raise HTTPException(400, detail=" ".join(ve.args)) from ve


@router.get(
    "/tickets/{state}",
    response_model=GenericListModel,
    tags=["Settings"],
    description="""Retrieve the ticket next states for a project""",
    responses={
        400: {
            "model": ErrorMessage,
            "description": "Project name is not a valid one. More than 63 characters or contains / \\ $ character",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        500: {"model": ErrorMessage, "description": "Error during server computing"},
    },
)
async def provide_next_ticket_states(
    project_name: str,
    state: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> GenericListModel:
    await project_version_raise(
        project_name,
    )
    try:
        if TicketType(state) not in ticket_authorized_transition:
            raise ValueError(f"'{state}' is not a valid project state.")
        else:
            return GenericListModel(data=ticket_authorized_transition[TicketType(state)])
    except ValueError as ve:
        raise HTTPException(400, detail=" ".join(ve.args)) from ve


@router.get(
    "/campaigns/{state}",
    response_model=GenericListModel,
    tags=["Settings"],
    description="""Retrieve the campaigns next states for a project - currently no enforced workflow""",
    responses={
        400: {
            "model": ErrorMessage,
            "description": "Project name is not a valid one. More than 63 characters or contains / \\ $ character",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
        500: {"model": ErrorMessage, "description": "Error during server computing"},
    },
)
async def provide_next_campaign_states(
    project_name: str,
    state: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> GenericListModel:
    await project_version_raise(
        project_name,
    )
    try:
        return GenericListModel(data=[item.value for item in CampaignStatusEnum if item != CampaignStatusEnum(state)])
    except ValueError as ve:
        raise HTTPException(400, detail=" ".join(ve.args)) from ve
