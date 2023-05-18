# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from psycopg.rows import dict_row

from app.app_exception import IncorrectFieldsRequest
from app.database.redis.token_management import revoke
from app.database.utils.password_management import get_password_hash
from app.utils.log_management import log_error, log_message
from app.utils.pgdb import pool


def init_user():
    with pool.connection() as conn:
        log_message("Init user")
        row = conn.execute("select id from users where username='admin@admin.fr'").fetchone()
        log_message(f"{row}")
        if row is None:
            create_user("admin@admin.fr", "admin", ["admin"])


def create_user(username, password, scopes):
    try:
        with pool.connection() as conn:
            log_message(f"Create user {username} with {scopes}")
            conn.execute("insert into users (username, password, scopes) "
                         " values (%s, %s, %s);",
                         (username, get_password_hash(password), scopes))
    except Exception as exception:
        log_error("\n".join(exception.args))
        raise


def get_user(username):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute("""select username, password, scopes
        from users
        where username = %s;
        """, (username,))
        return rows.fetchone()


def update_user(username, password=None, scopes=None):
    user = get_user(username)
    upsert = False if user is None else True

    with pool.connection() as conn:
        if upsert:
            if password is not None:
                row = conn.execute("update users "
                                   " set password = %s "
                                   " where username = %s "
                                   " returning id;",
                                   (get_password_hash(password), username))
            if scopes is not None:
                row = conn.execute("update users "
                                   " set scopes = %s "
                                   " where username = %s "
                                   " returning id;",
                                   (scopes, username))
        else:
            if password is None or password == "":
                raise IncorrectFieldsRequest("Cannot create user without password")

            row = conn.execute("insert into users (username, password, scopes) "
                               " values (%s, %s, %s) "
                               " returning id;",
                               (username, get_password_hash(password), scopes)
                               )
    return row.fetchone()[0]


def self_update_user(username, new_password):
    result = update_user(username, new_password)
    revoke(username)
    return result
