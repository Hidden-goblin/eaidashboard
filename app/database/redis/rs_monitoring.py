# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.utils.redis import redis_connection


def rs_health() -> bool:
    """
    Check if redis answers the ping
    Returns: bool
    """
    connection = redis_connection()
    return connection.ping()
