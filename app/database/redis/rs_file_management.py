# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from os import remove
from pathlib import Path

from app.conf import BASE_DIR
from app.utils.log_management import log_message
from app.utils.redis import redis_connection


async def rs_record_file(
    file_key: str,
    filename: str,
) -> str:
    # SPEC: record an entry file_key-filename in redis
    # SPEC: file_key should match file:project_alias:version:occurrence:type
    connection = redis_connection()
    await connection.set(
        file_key,
        filename,
    )
    return str(connection.get(file_key))


async def rs_invalidate_file(
    file_key_pattern: str,
) -> None:
    # SPEC: remove file_key from storage
    # SPEC: remove real file if file exists
    connection = redis_connection()
    keys = await connection.keys(file_key_pattern)
    for key in keys:
        filename = Path(f"{BASE_DIR}/static/{connection.get(key).decode()}")
        if filename.exists():
            remove(filename)
        else:
            log_message(f"File {filename.name} does not exist anymore")
    if keys:
        await connection.delete(*keys)


async def rs_retrieve_file(
    file_key: str,
) -> str | None:
    # SPEC: return stored filename or None if not exists
    # SPEC: check real file exists invalidate and return None if not
    connection = redis_connection()
    _filename = await connection.get(file_key)
    filename = _filename.decode() if _filename is not None else None
    if filename is not None:
        filepath = Path(f"{BASE_DIR}/static/{filename}")
        if filepath.exists():
            return filename
        else:
            await rs_invalidate_file(file_key)
    return None
