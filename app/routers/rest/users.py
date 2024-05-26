# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from fastapi import APIRouter, HTTPException, Security
from starlette.responses import Response

from app.app_exception import IncorrectFieldsRequest, InvalidDeletion, ProjectNotRegistered, UserNotFoundException
from app.database.authentication import authenticate_user
from app.database.authorization import authorize_user
from app.database.postgre.pg_users import (
    create_user,
    db_delete_user,
    get_user,
    get_users,
    self_update_user,
    update_user,
)
from app.schema.error_code import ErrorMessage
from app.schema.project_schema import RegisterVersionResponse
from app.schema.users import UpdateMe, UpdateUser, User, UserLight

router = APIRouter(
    prefix="/api/v1"
)


@router.get("/users",
            tags=["Users"],
            description="""Retrieve all users with their scopes.

With the `is_list=true` retrieve only the usernames.

By default, gather all users (everyone is in the special project `*`).

Using a project name and `included=false`, retrieve all users not in this specific project.
Application administrator are excluded.""",
            response_model=List[UserLight | str])
async def all_users(response: Response,
                    limit: int = 10,
                    skip: int = 0,
                    is_list: bool = False,
                    project: str = "*",
                    included: bool = True,
                    user: User = Security(authorize_user, scopes=["admin"])) -> List[UserLight | str]:
    try:
        if is_list:
            return get_users(is_list=is_list, project_name=project, included=included)
        users, count = get_users(limit=limit, skip=skip, project_name=project, included=included)
        response.headers["X-total-count"] = str(count)
        return users
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp


@router.get("/users/{username}",
            tags=["Users"],
            description="Retrieve one user with his scopes",
            response_model=UserLight)
async def one_user(username: str,
                   response: Response,
                   user: User = Security(authorize_user, scopes=["admin"])) -> UserLight:
    try:

        _user = get_user(username)
        if _user is None:
            raise UserNotFoundException(
                f"User '{username}' is not found.")
        return _user
    except UserNotFoundException as unfe:
        raise HTTPException(404, ", ".join(unfe.args)) from unfe
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp


@router.put("/users/me",
            tags=["Users"],
            description="""Self update. Only registered users can update their data.""",
            response_model=RegisterVersionResponse,
            responses={
                401: {"model": ErrorMessage,
                      "description": "Cannot authenticate the user"}
            })
async def update_me(body: UpdateMe,
                    user: User = Security(
                        authorize_user, scopes=["admin", "user"])) -> RegisterVersionResponse:
    try:
        # If success register token with a ttl
        _user = authenticate_user(user["username"], body.password)
        if _user is None:
            raise HTTPException(401, "Unrecognized credentials")
        return self_update_user(username=user["username"], new_password=body.new_password)
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp


@router.patch("/users",
              tags=["Users"],
              description="""Update a user. Only admin can do so.""",
              response_model=RegisterVersionResponse)
async def patch_user(body: UpdateUser,
                     user: User = Security(
                         authorize_user, scopes=["admin"])) -> RegisterVersionResponse:
    try:
        return update_user(body)
    except IncorrectFieldsRequest as ifr:
        raise HTTPException(400, ", ".join(ifr.args)) from ifr
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, ", ".join(pnr.args)) from pnr
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp


@router.post("/users",
             tags=["Users"],
             description="""Update a user. Only admin can do so.""",
             response_model=RegisterVersionResponse)
async def create_update(body: UpdateUser,
                        user: User = Security(
                            authorize_user, scopes=["admin"])) -> RegisterVersionResponse:
    try:
        return create_user(body)
    except IncorrectFieldsRequest as ifr:
        raise HTTPException(400, ", ".join(ifr.args)) from ifr
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, ", ".join(pnr.args)) from pnr
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp


@router.delete("/users/{username}",
               status_code=204,
               tags=["Users"],
               description="""Update a user. Only admin can do so.""",
               response_class=Response,
               responses={
                   401: {"model": ErrorMessage,
                         "description": "Cannot authenticate the user"},
                   400: {"model": ErrorMessage,
                         "description": "One of the delete business rule is not met"}
               })
async def delete_user(username: str,
                      user: User = Security(
                          authorize_user, scopes=["admin"])) -> None:
    try:
        db_delete_user(username)
    except InvalidDeletion as _id:
        raise HTTPException(400, ', '.join(_id.args)) from _id
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp


@router.get("/projects/{project_name}/users",
            tags=["Users", "Projects"],
            description="""Get users linked to a projects""",
            response_model=List[UserLight | str])
async def all_users_in_project(project_name: str,
                               response: Response,
                               limit: int = 10,
                               skip: int = 0,
                               is_list: bool = False,
                               user: User = Security(authorize_user, scopes=["admin"])) -> List[UserLight | str]:
    pass
