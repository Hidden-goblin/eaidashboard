# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

import redis
from redis.client import Redis
from redis.exceptions import ConnectionError

import app.utils.redis
from app.conf import redis_dict

redis_pool = None


def redis_health() -> bool:
    try:
        conn = redis_connection()
        return conn.ping()
    except ConnectionError:
        print("Redis connection error")
        return False


def redis_connection() -> Redis[bytes]:
    if app.utils.redis.redis_pool is None:
        app.utils.redis.redis_pool = redis.ConnectionPool(**redis_dict, db=0)

    return redis.Redis(connection_pool=app.utils.redis.redis_pool)
