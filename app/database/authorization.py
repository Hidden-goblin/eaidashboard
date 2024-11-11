# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import re
from logging import getLogger

import jwt.exceptions
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from starlette import status
from starlette.requests import Request

from app.conf import templates
from app.database.postgre.pg_users import get_user
from app.database.redis.token_management import get_token_date, renew_token_date
from app.database.utils.token import token_scope, token_user
from app.schema.users import User
from app.utils.log_management import log_error

log = getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/token", scopes={"admin": "All operations granted", "user": "Update"}
)


def path_project(request: Request) -> str:
    # TODO check if the regex match the project naming constraints
    res = re.match(r".*/(api|front)/v[0-9]/projects/(?P<project_name>[\w \-]+)", str(request.url))
    return res["project_name"] if res is not None else None


def authorize_user(
    security_scopes: SecurityScopes,
    token: str = Depends(
        oauth2_scheme,
    ),
    project_name: str = Depends(path_project),
) -> User | HTTPException:
    return __generic_authorization(security_scopes, token, project_name)


def __generic_authorization(
    security_scopes: SecurityScopes,
    token: str,
    project_name: str,
) -> User | HTTPException:
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
        user = get_user(email, True)
        if user is None:
            raise credentials_exception

        # Check token validity
        get_token_date(user.username)
        if get_token_date(user.username) is None:
            raise credentials_exception

        # Check user right
        token_scopes = token_scope(token)
    except jwt.InvalidSignatureError as ise:
        log_error("JWT has an invalid signature.")
        raise credentials_exception from ise
    except Exception as exception:
        log_error("\n".join(exception.args))
        raise credentials_exception from exception
    # Raise if the user has no matching scope
    if (
        token_scopes.right(project_name=project_name) is None
        or token_scopes.right(project_name=project_name) not in security_scopes.scopes
    ) and security_scopes.scopes:
        raise HTTPException(403, "You are not authorized to access this resource.")
    renew_token_date(user.username)

    return user


def front_authorize(
    security_scopes: SecurityScopes,
    request: Request,
    project_name: str = Depends(path_project),
) -> User:
    try:
        return __generic_authorization(security_scopes, request.session.get("token"), project_name)
    except Exception:
        return templates.TemplateResponse(
            "error_message.html",
            {
                "request": request,
                "highlight": "You are not authorized",
                "sequel": " to perform this action.",
                "advise": "Try to log again.",
            },
            headers={"HX-Retarget": "#messageBox"},
        )
