# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from psycopg.rows import dict_row

from app.conf import config
from app.utils.pgdb import pool


def pg_health() -> dict:
    """
    Check the postgresql db
    Returns: dict, {"connections": <number of connections>, "in_recovery": bool}
    """
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            "select count(*) as connections" " from pg_stat_activity" " where datname = %s;",
            (config["PG_DB"],),
        )

        recovery = connection.execute("select pg_is_in_recovery() as in_recovery")

        return {"connections": rows.fetchone()["connections"], "in_recovery": recovery.fetchone()["in_recovery"]}
