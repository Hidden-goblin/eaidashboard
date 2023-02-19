# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime, timezone

import redis
from app.conf import (redis_dict, config)

EXPIRE_LIMIT = 60 * int(config['TIMEDELTA'])

def get_token_date(username):
    connection = redis.Redis(**redis_dict, db=0)
    return connection.get(f"{username}:token")

def renew_token_date(username):
    connection = redis.Redis(**redis_dict, db=0)
    connection.expire(f"{username}:token", EXPIRE_LIMIT)

def register_connection(username):
    connection = redis.Redis(**redis_dict, db=0)
    count =  len(connection.keys("*:token"))
    connection.set(f"{username}:token", str(datetime.now(timezone.utc)))
    connection.expire(f"{username}:toke", EXPIRE_LIMIT)
    return count

def revoke(username):
    connection = redis.Redis(**redis_dict, db=0)
    connection.delete(f"{username}:token")
