# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from jwt import decode

from app import conf
from app.schema.authentication import Scopes


def token_user(token: str | bytes) -> str:
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return payload.get("sub")


def token_scope(token: str | bytes) -> Scopes:
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return Scopes(scopes=payload.get("scopes", {"*": None}))
