# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
from typing import List, Tuple

from jwt import decode, encode

from app import conf
from app.database.postgre.pg_users import get_user
from app.database.redis.token_management import register_connection, revoke
from app.database.utils.password_management import generate_keys, verify_password


def authenticate_user(username: str, password: str) -> Tuple[str | None, List[str]]:
    try:
        user = get_user(username)
        if user and verify_password(password, user["password"]):
            return user["username"], user["scopes"]
        else:
            return None, []
    except Exception as exception:
        log = logging.getLogger("uvicorn.access")
        log.warning(msg=" ".join(exception.args))
        return None, []


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    if not register_connection(data):
        generate_keys()

    return encode(to_encode, conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def invalidate_token(token: str | bytes) -> None:
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    revoke(payload.get("sub"))
