# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from contextlib import asynccontextmanager
import redis.asyncio as redis
from redis.exceptions import ConnectionError
from app.conf import redis_dict


async def redis_health():
    try:
        async with redis_connection() as conn:
            return await conn.ping()
    except ConnectionError:
        print("Redis connection error")
        return False

@asynccontextmanager
async def redis_connection():
    connection = redis.Redis(**redis_dict, db=0)
    try:
        yield connection
    finally:
        await connection.close()


