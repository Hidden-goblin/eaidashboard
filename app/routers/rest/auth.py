# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Security
from fastapi.security import OAuth2PasswordRequestForm
from jwt import DecodeError
from starlette.responses import Response

from app.database.authentication import (
    authenticate_user,
    create_access_token,
    invalidate_token,
)
from app.database.authorization import (
    authorize_user,
    oauth2_scheme,
)
from app.schema.authentication import TokenData
from app.schema.error_code import ErrorMessage
from app.schema.users import TokenResponse, User
from app.utils.log_management import log_error

router = APIRouter(prefix="/api/v1")


@router.post(
    "/token",
    tags=["Users"],
    description="Retrieve a JWT token to access the application",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorMessage, "description": "User and/or password not recognized. Could not provide a JWT"}
    },
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = authenticate_user(
        form_data.username,
        form_data.password,
    )
    if user is None:
        raise HTTPException(401, detail="Unrecognized credentials")
    access_token = create_access_token(
        data=TokenData(
            sub=user.username,
            scopes=user.scopes,
        ),
    )
    return TokenResponse(access_token=access_token)


@router.delete(
    "/token",
    tags=["Users"],
    description="Invalidate the current token.",
    status_code=204,
    responses={
        401: {
            "model": ErrorMessage,
            "description": "The providen token has already been invalidated.",
        }
    },
)
async def expire_access_token(
    user: User = Security(authorize_user, scopes=[]),
    token: str = Depends(
        oauth2_scheme,
    ),
) -> Response:
    try:
        invalidate_token(token)
        return Response(status_code=204)
    except DecodeError as ve:
        log_error(repr(ve))
        raise HTTPException(401, detail="JWT error") from ve
