# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
from typing import List, Tuple

import psycopg.errors
from psycopg.rows import dict_row, tuple_row
from psycopg.types.json import Json

from app.app_exception import IncorrectFieldsRequest, ProjectNotRegistered
from app.database.redis.token_management import revoke
from app.database.utils.password_management import get_password_hash
from app.schema.project_schema import RegisterVersionResponse
from app.schema.users import UpdateUser, User, UserLight
from app.utils.log_management import log_error, log_message
from app.utils.pgdb import pool
from app.utils.project_alias import contains


class UserUpdate:
    pass


def init_user() -> None:
    with pool.connection() as conn:
        log_message("Init user")
        row = conn.execute("select id from users where username='admin@admin.fr'").fetchone()
        log_message(f"{row}")
        if row is None:
            create_user(
                UpdateUser(username="admin@admin.fr", password="admin", scopes={"*": "admin"}))


def create_user(user: UpdateUser) -> RegisterVersionResponse:
    log_message(f"Create user {user.username} with {user.scopes}")
    if user.password is None or user.password == "":
        raise IncorrectFieldsRequest("Cannot create user without password")
    _check_scopes(user.scopes)
    try:
        with pool.connection() as conn:
            log_message(f"Create user {user.username} with {user.scopes}")
            conn.row_factory = tuple_row
            row = conn.execute("insert into users (username, password, scopes) "
                               " values (%s, %s, %s)"
                               " returning id;",
                               (user.username, get_password_hash(user.password),
                                json.dumps(user.scopes)))
            return RegisterVersionResponse(inserted_id=str(row.fetchone()[0]))
    except psycopg.errors.UniqueViolation as uve:
        log_error("\n".join(uve.args))
        raise
    except Exception as exception:
        log_error("\n".join(exception.args))
        raise


def _check_scopes(scopes: dict) -> None:
    """Check scope content so that cannot assign to a user rights on non-existing project"""
    zipped_project_oracle = list(zip([contains(project) or project == "*" for project in scopes],
                                     scopes.keys()))
    if not all(project[0] for project in zipped_project_oracle):
        raise ProjectNotRegistered(
            f"The projects '"
            f"{', '.join(project[1] for project in zipped_project_oracle if not project[0])}"
            f"' are not registered.")


def get_user(username: str, is_light: bool = True) -> User | UserLight |None:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute("""select username, password, scopes
        from users
        where username = %s;
        """, (username,))
        temp = rows.fetchone()
        if is_light:
            return UserLight(username=temp["username"],
                             scopes=temp["scopes"]) if temp is not None else None
        return User(username=temp["username"],
                    password=temp["password"],
                    scopes=temp["scopes"]) if temp is not None else None


def get_users(limit: int = 10,
              skip: int = 0,
              is_list: bool = False) -> Tuple[List[UserLight], int] | List[str]:
    if is_list:
        return __list_of_users()

    with pool.connection() as connection1:
        connection1.row_factory = None
        connection1.row_factory = dict_row
        rows = connection1.execute("select username, scopes"
                                  " from users"
                                  " order by username"
                                  " limit %s"
                                  " offset %s;", (limit, skip))
        count = connection1.execute("select count(distinct username) as count from users;")
        return [UserLight(**row) for row in rows.fetchall()], int(count.fetchone()["count"])


def __list_of_users() -> List[str]:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        rows = connection.execute("select username"
                                  " from users"
                                  " order by username;")
        return [row[0] for row in rows.fetchall()]


def update_user(user: UpdateUser) -> RegisterVersionResponse:
    _user = get_user(user.username)
    upsert = _user is not None
    if not upsert:
        return create_user(user)

    with pool.connection() as conn:
        conn.row_factory = tuple_row

        log_message(f"Update user {user.username} with updated {user.scopes} scopes")
        if user.password is not None:
            row = conn.execute("update users "
                               " set password = %s "
                               " where username = %s "
                               " returning id;",
                               (get_password_hash(user.password), user.username))
        if user.scopes is not None:
            # Check project: include special project "*"
            _check_scopes(user.scopes)
            # Combine actual with to be scope
            merged_scopes = {**_user.scopes,
                             **user.scopes}
            row = conn.execute("update users "
                               " set scopes = %s "
                               " where username = %s "
                               " returning id;",
                               (Json(merged_scopes), user.username))
            return RegisterVersionResponse(inserted_id=str(row.fetchone()[0]))


def self_update_user(username: str, new_password: str) -> RegisterVersionResponse:
    result = update_user(UpdateUser(username=username, password=new_password))
    revoke(username)
    return result
