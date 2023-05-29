# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Security
from fastapi.security import OAuth2PasswordRequestForm
from jwt import DecodeError

from app.database.authentication import authenticate_user, create_access_token
from app.database.authorization import authorize_user
from app.database.redis.token_management import revoke
from app.utils.log_management import log_error

router = APIRouter(
    prefix="/api/v1"
)


@router.post("/token",
             tags=["Users"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    sub, scopes = authenticate_user(form_data.username, form_data.password)
    if sub is None:
        raise HTTPException(401, detail="Unrecognized credentials")
    access_token = create_access_token(
        data={"sub": sub,
              "scopes": scopes})
    return {"access_token": access_token, "token_type": "Bearer"}


@router.delete("/token",
               tags=["Users"])
async def expire_access_token(user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        revoke(user["username"])
        return {}
    except DecodeError as ve:
        log_error(repr(ve))
        raise HTTPException(401, detail="JWT error") from ve
