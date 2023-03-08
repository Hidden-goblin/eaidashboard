# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
from jwt import encode, decode

from app import conf
from app.database.utils.password_management import generate_keys, verify_password

from app.database.redis.token_management import register_connection, revoke
from app.database.postgre.pg_users import get_user


def authenticate_user(username, password):
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

def create_access_token(data: dict):
    to_encode = data.copy()
    if not register_connection(data):
        generate_keys()

    return encode(to_encode, conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def invalidate_token(token):
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    revoke(payload.get("sub"))
