# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from fastapi import APIRouter, HTTPException, Security

from app import conf
from app.database.authentication import authenticate_user
from app.database.authorization import authorize_user
if conf.MIGRATION_DONE:
    from app.database.postgre.pg_users import (self_update_user, update_user)
else:
    from app.database.mongo.users import (self_update_user, update_user)
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
    username, scope = authenticate_user(user["username"], body.dict()["password"])
    if username is None:
        raise HTTPException(401, "Unrecognized credentials")
    return self_update_user(username=user["username"], new_password=body.dict()["new_password"])


@router.post("/",
             tags=["Users"],
             description="""Update a user. Only admin can do so.""")
async def create_update(body: UpdateUser,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    result = update_user(**body.dict())
    return result is not None
