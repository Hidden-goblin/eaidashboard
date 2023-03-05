# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from jwt import decode

from app import conf


def token_user(token):
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return payload.get("sub")


def token_scope(token):
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return payload.get("scopes", [])
