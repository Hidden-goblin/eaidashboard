# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from jwt import decode

from app import conf
from app.schema.authentication import Scopes


def _validate_token_format(token: str) -> str:
    if token and isinstance(token, str) and token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    return token


def token_user(token: str | bytes) -> str:
    token = _validate_token_format(token)
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return payload.get("sub")


def token_scope(token: str | bytes) -> Scopes:
    token = _validate_token_format(token)
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return Scopes(scopes=payload.get("scopes", {"*": None}))
