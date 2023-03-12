# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.utils.redis import redis_connection


async def rs_record_file(file_key: str, filename: str) -> str:
    # SPEC: record an entry file_key-filename in redis
    # SPEC: file_key should match file:project_alias:version:occurrence:type
    connection = redis_connection()
    connection.set(file_key, filename)
    return str(connection.get(file_key))

async def rs_invalidate_file(file_key_pattern: str):
    # SPEC: remove file_key from storage
    connection = redis_connection()
    keys = connection.keys(file_key_pattern)
    connection.delete(*keys)

async def rs_retrieve_file(file_key: str):
    # SPEC: return stored filename or None if not exists
    connection = redis_connection()
    filename = connection.get(file_key)
    return filename.decode() if filename is not None else None