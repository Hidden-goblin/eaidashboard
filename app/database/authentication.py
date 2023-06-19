# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging

from jwt import decode, encode

from app import conf
from app.database.postgre.pg_users import get_user
from app.database.redis.token_management import register_connection, revoke
from app.database.utils.password_management import generate_keys, verify_password
from app.schema.authentication import TokenData
from app.schema.users import User


def authenticate_user(username: str, password: str) -> User | None:
    try:
        user = get_user(username)
        return user if verify_password(password, user["password"]) else None
    except Exception as exception:
        log = logging.getLogger("uvicorn.access")
        log.warning(msg=" ".join(exception.args))
        return None


def create_access_token(data: TokenData) -> str:
    if not register_connection(data):
        generate_keys()

    return encode(data.to_dict(), conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def invalidate_token(token: str | bytes) -> None:
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    revoke(payload.get("sub"))
