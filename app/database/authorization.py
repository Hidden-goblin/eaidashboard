# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt import decode, PyJWTError
from pydantic import ValidationError
from pymongo import MongoClient
from starlette import status

from app.conf import mongo_string
from app.database.authentication import ALGORITHM, PUBLIC_KEY
from app.schema.authentication import TokenData


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
    return user
