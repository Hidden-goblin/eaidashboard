# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import jwt.exceptions
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt import decode, PyJWTError
from pydantic import ValidationError
from pymongo import MongoClient
from starlette import status
from starlette.requests import Request
from logging import getLogger

from app.app_exception import NotAuthorized, NotConnected
from app.conf import mongo_string
from app.database.authentication import ALGORITHM, PUBLIC_KEY
from app.schema.authentication import TokenData

log = getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/token",
    scopes={"admin": "All operations granted",
            "user": "Update"}
)


def authorize_user(security_scopes: SecurityScopes,
                   token: str = Depends(oauth2_scheme)):
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
        payload = decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, email=email)
    except (PyJWTError, ValidationError) as ex:
        raise credentials_exception from ex
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]
    user = collection.find_one({"username": email}, projection={"scopes": True, "username": True})
    if user is None:
        raise credentials_exception
    if all(scope not in security_scopes.scopes for scope in token_data.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )
    # Check disconnected
    to_disable = db["token"].find_one({"username": email})
    if to_disable is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reconnect",
            headers={"WWW-Authenticate": authenticate_value},
        )

    return user


def is_updatable(request: Request, rights: tuple) -> bool:
    if "token" not in request.session:
        return False
    try:
        check_authorization(request.session["token"], rights)
        return True
    except Exception as ex:
        log.error("".join(ex.args))
        return False


def check_authorization(token, rights: tuple):
    payload = decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
    email: str = payload.get("sub")
    if email is None:
        raise NotConnected("Not connected")
    token_scopes = payload.get("scopes", [])
    token_data = TokenData(scopes=token_scopes, email=email)
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]
    user = collection.find_one({"username": email}, projection={"scopes": True, "username": True})
    if user is None:
        raise NotAuthorized("User not recognized")
    if all(scope not in rights for scope in token_data.scopes):
        raise NotAuthorized("Not enough rights")


def check_token_validity(request: Request):
    if "token" not in request.session:
        return False
    try:
        payload = decode(request.session["token"], PUBLIC_KEY, algorithms=[ALGORITHM])
    except jwt.exceptions.ExpiredSignatureError:
        log.info("Signature expired")
        return False
    email: str = payload.get("sub")
    if email is None:
        return False

    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["token"]
    user = collection.find_one({"username": email})
    return bool(user)
