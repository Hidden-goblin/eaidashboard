# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from fastapi import APIRouter, Security

from app.database.authorization import authorize_user
from app.database.users import self_update_user, update_user

router = APIRouter(
    prefix="/api/v1/users"
)


@router.put("/me")
async def update_me(body: dict,
                    user: Any = Security(authorize_user, scopes=["admin", "user"])):
    return self_update_user(**{**body, "username": user["username"]})


@router.post("/")
async def create_update(body: dict,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    result = update_user(**body)
    return result is not None
