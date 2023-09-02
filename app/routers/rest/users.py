# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from fastapi import APIRouter, HTTPException, Security
from starlette.responses import Response

from app.app_exception import IncorrectFieldsRequest, ProjectNotRegistered, UserNotFoundException
from app.database.authentication import authenticate_user
from app.database.authorization import authorize_user
from app.database.postgre.pg_users import get_user, get_users, self_update_user, update_user
from app.schema.project_schema import ErrorMessage, RegisterVersionResponse
from app.schema.users import UpdateMe, UpdateUser, User, UserLight

router = APIRouter(
    prefix="/api/v1/users"
)


@router.get("/",
            tags=["Users"],
            description="Retrieve all users with their scope",
            response_model=List[UserLight | str])
async def all_users(response: Response,
                    limit: int = 10,
                    skip: int = 0,
                    is_list: bool = False,
                    user: User = Security(authorize_user, scopes=["admin"])) -> List[UserLight | str]:
    try:
        if is_list:
            return get_users(is_list=is_list)
        users, count = get_users(limit=limit, skip=skip)
        response.headers["X-total-count"] = str(count)
        return users
    except Exception as exp:
        raise HTTPException(500, ", ".join(exp.args)) from exp

@router.get("/{username}",
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
@router.put("/me",
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


@router.post("/",
             tags=["Users"],
             description="""Update a user. Only admin can do so.""",
             response_model=RegisterVersionResponse)
async def create_update(body: UpdateUser,
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
