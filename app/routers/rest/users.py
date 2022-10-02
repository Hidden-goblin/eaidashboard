# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from fastapi import APIRouter, Security

from app.database.authorization import authorize_user
from app.database.users import self_update_user, update_user
from app.schema.users import UpdateMe, UpdateUser

router = APIRouter(
    prefix="/api/v1/users"
)


@router.put("/me",
            tags=["Users"],
            description="""Self update. Only registered users can update their data.""")
async def update_me(body: UpdateMe,
                    user: Any = Security(authorize_user, scopes=["admin", "user"])):
    # If success register token with a ttl
    return self_update_user(**{**body.dict(), "username": user["username"]})


@router.post("/",
             tags=["Users"],
             description="""Update a user. Only admin can do so.""")
async def create_update(body: UpdateUser,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    result = update_user(**body.dict())
    return result is not None
