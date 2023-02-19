# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from psycopg.rows import dict_row

from app.utils.pgdb import pool


def init_user():
    pass

def get_user(username):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute("""select username, password, scopes  
        from users
        where username = %s;
        """, (username,))
        return rows.fetch_one()

def update_user(username, password=None, scopes=None):
    pass

def self_update_user(username, new_password):
    pass
