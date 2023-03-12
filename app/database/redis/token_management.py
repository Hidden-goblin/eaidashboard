# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json

from app.conf import config
from app.utils.redis import redis_connection

EXPIRE_LIMIT = 60 * int(config['TIMEDELTA'])

def get_token_date(username):
    connection = redis_connection()
    count = connection.keys("*:token")
    return connection.get(f"{username}:token")

def renew_token_date(username):
    connection = redis_connection()
    connection.expire(f"{username}:token", EXPIRE_LIMIT)

def register_connection(username):
    connection = redis_connection()
    count =  len(connection.keys("*:token"))
    connection.set(f"{username['sub']}:token", json.dumps(username))
    connection.expire(f"{username['sub']}:token", EXPIRE_LIMIT)
    return count

def revoke(username):
    connection = redis_connection()
    connection.delete(f"{username}:token")
