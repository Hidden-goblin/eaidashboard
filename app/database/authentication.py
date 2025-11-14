# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging

from jwt import decode, encode

from app import conf
from app.database.postgre.pg_users import get_user, update_user_password
from app.database.redis.token_management import register_connection, revoke
from app.database.utils.password_management import generate_keys, verify_password
from app.schema.authentication import TokenData
from app.schema.users import UpdateUser, User


def authenticate_user(username: str, password: str) -> User | None:
    try:
        user = get_user(username, False)
        is_authenticated, new_hash = verify_password(password, user["password"])
        if is_authenticated:
            return maybe_update_password_hash(user, new_hash, password)

    except Exception as exception:
        log = logging.getLogger("uvicorn.access")
        log.warning(msg=" ".join(exception.args))
        return None


def maybe_update_password_hash(user: User, new_hash: str | None, password: str) -> User:
    if new_hash is None:
        return user
    update_user_password(UpdateUser(username=user.username, password=password))
    return user


def create_access_token(data: TokenData) -> str:
    if not register_connection(data):
        generate_keys()

    return encode(data.to_dict(), conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def invalidate_token(token: str | bytes) -> None:
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    revoke(payload.get("sub"))
