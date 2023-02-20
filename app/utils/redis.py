# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

import redis
from redis.exceptions import ConnectionError
from app.conf import redis_dict

redis_pool = None

def redis_health():
    try:
        conn = redis_connection()
        return conn.ping()
    except ConnectionError:
        print("Redis connection error")
        return False


def redis_connection():
    if redis_pool is None:
        redis_pool = redis.ConnectionPool(**redis_dict, db=0)
    
    return redis.Redis(connection_pool=redis_pool)


