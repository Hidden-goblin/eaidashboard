# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import jwt.exceptions
from app import conf
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt import decode, PyJWTError
from pydantic import ValidationError
from pymongo import MongoClient
from starlette import status
from starlette.requests import Request
from logging import getLogger

if conf.MIGRATION_DONE:
    from app.database.redis.token_management import (get_token_date,
                                                     renew_token_date)
    from app.database.postgre.pg_users import get_user
else:
    from app.database.mongo.tokens import (get_token_date,
                                           renew_token_date)
    from app.database.mongo.users import get_user

from app.database.utils.token import token_scope, token_user
from app.schema.authentication import TokenData

log = getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/token",
    scopes={"admin": "All operations granted",
            "user": "Update"}
)


def authorize_user(security_scopes: SecurityScopes,
                   token: str = Depends(oauth2_scheme)):
    # Error message building
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        # Authorize method
        # Token contains the username
        email = token_user(token)
        if email is None:
            raise credentials_exception

        # Check user in db
        user = get_user(email)
        if user is None:
            raise credentials_exception

        # Check token validity
        if get_token_date(user["username"]) is None:
            raise credentials_exception

        # Check user right
        token_scopes = token_scope(token)
        token_data = TokenData(scopes=token_scopes, email=email)
    except jwt.InvalidSignatureError:
        raise credentials_exception
    if (all(scope not in security_scopes.scopes for scope in token_data.scopes)
            and security_scopes.scopes):
        raise credentials_exception
    renew_token_date(user["username"])

    return user


def is_updatable(request: Request, rights: tuple) -> bool:
    """Authorization method for front usage"""
    if "token" not in request.session:
        return False
    try:
        authorize_user(SecurityScopes(list(rights)), request.session["token"])
        return True
    except Exception as ex:
        log.error("".join(ex.args))
        return False
