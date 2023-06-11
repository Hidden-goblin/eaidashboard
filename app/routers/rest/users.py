# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter, HTTPException, Security

from app.database.authentication import authenticate_user
from app.database.authorization import authorize_user
from app.database.postgre.pg_users import self_update_user, update_user
from app.schema.project_schema import ErrorMessage, RegisterVersionResponse
from app.schema.users import UpdateMe, UpdateUser

router = APIRouter(
    prefix="/api/v1/users"
)


@router.put("/me",
            tags=["Users"],
            description="""Self update. Only registered users can update their data.""",
            response_model=RegisterVersionResponse,
            responses={
                401: {"model": ErrorMessage,
                      "description": "Cannot authenticate the user"}
            })
async def update_me(body: UpdateMe,
                    user: UpdateUser = Security(
                        authorize_user, scopes=["admin", "user"])) -> RegisterVersionResponse:
    try:
        # If success register token with a ttl
        username, scope = authenticate_user(user["username"], body.dict()["password"])
        if username is None:
            raise HTTPException(401, "Unrecognized credentials")
        return self_update_user(username=user["username"], new_password=body.dict()["new_password"])
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.post("/",
             tags=["Users"],
             description="""Update a user. Only admin can do so.""",
             response_model=RegisterVersionResponse)
async def create_update(body: UpdateUser,
                        user: UpdateUser = Security(
                            authorize_user, scopes=["admin"])) -> RegisterVersionResponse:
    try:
        result = update_user(**body.dict())
        return result
    except Exception as exp:
        raise HTTPException(500, repr(exp))
