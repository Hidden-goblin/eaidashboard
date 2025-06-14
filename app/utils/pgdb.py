# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Callable, ContextManager, Optional

from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.conf import config

pool = ConnectionPool(
    f"host={config['PG_URL']} port={config['PG_PORT']} user={config['PG_USR']}"
    f" password={config['PG_PWD']} dbname={config['PG_DB']}",
    open=True,
    num_workers=6,
)


def get_connection(row_factory: Optional[Callable[..., object]] = None) -> ContextManager[Connection]:
    """
    Helper to get a connection with an optional row factory.
    """
    conn = pool.connection()
    if row_factory:
        conn.row_factory = row_factory
    return conn
