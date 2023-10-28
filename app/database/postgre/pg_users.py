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
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.project_schema import RegisterVersionResponse
from app.schema.users import UpdateUser, User, UserLight
from app.utils.log_management import log_error, log_message
from app.utils.pgdb import pool
from app.utils.project_alias import contains


def init_user() -> None:
    """Create the default admin profile"""
    with pool.connection() as conn:
        log_message("Init user")
        row = conn.execute("select id from users where username='admin@admin.fr'").fetchone()
        log_message(f"{row}")
        if row is None:
            create_user(
                UpdateUser(username="admin@admin.fr", password="admin", scopes={"*": "admin"}))


def create_user(user: UpdateUser) -> RegisterVersionResponse:
    """
    SPEC Cannot create a user without a password and a username
    SPEC Cannot create a user which scopes contain non-existing project
    SPEC Without scopes, add user scope for "*" project
    :param user:
    :return: RegisterVersionResponse
    """
    log_message(f"Create user {user.username} with {user.scopes}")
    if user.password is None or user.password == "":
        raise IncorrectFieldsRequest("Cannot create user without password")
    if user.scopes:
        _check_scopes(user.scopes)
    else:
        user.scopes["*"] = "user"
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
    except TypeError as te:
        log_error("\n".join(te.args))
        raise
    except ValueError as ve:
        log_error("\n".join(ve.args))
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


def get_user(username: str,
             is_light: bool = True) -> User | UserLight | None:
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
              is_list: bool = False,
              project_name: str = None,
              included: bool = True) -> Tuple[List[UserLight], int] | List[str]:
    """

    :param limit: default 10 (only for list of UserLight)
    :param skip: default 0 (only for list of UserLight)
    :param is_list: only the usernames as a list
    :param project_name: filter users regarding the project
    :param included: additional filtering related to project_name filter. Included in project_name or excluded
    :return:
    """
    if is_list:
        expected_list = {False: __list_of_user_not_in_project,
                         True: __list_of_users}
        return expected_list[included](project_name=project_name)

    if project_name is None or project_name == "*":
        return __all_users(limit, skip)
    return __users_in_project(project_name, limit, skip)


def __all_users(limit: int = 10,
                skip: int = 0) -> Tuple[List[UserLight], int]:
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


def __users_in_project(project_name: str,
                       limit: int = 10,
                       skip: int = 0) -> Tuple[List[UserLight], int]:
    with pool.connection() as connection1:
        connection1.row_factory = None
        connection1.row_factory = dict_row
        rows = connection1.execute("select username, scopes"
                                   " from users"
                                   " where scopes::jsonb ?| %s"
                                   " or scopes ->> '*' = 'admin'"
                                   " order by username"
                                   " limit %s"
                                   " offset %s;", (f'{{{project_name}}}', limit, skip))
        count = connection1.execute("select count(distinct username) as count from users where scopes::jsonb ?| %s"
                                    " or scopes ->> '*' = 'admin';", (f'{{{project_name}}}',))
        return [UserLight(**row) for row in rows.fetchall()], int(count.fetchone()["count"])


def __list_of_users(project_name: str = "*") -> List[str]:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        rows = connection.execute("select username"
                                  " from users"
                                  " where scopes::jsonb ?| %s"
                                  " or scopes ->> '*' = 'admin'"
                                  " order by username;", (f'{{{project_name}}}',))
        return [row[0] for row in rows.fetchall()]


def __list_of_user_not_in_project(project_name: str) -> List[str]:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        rows = connection.execute("select username"
                                  " from users"
                                  " where not (scopes::jsonb ?| %s)"
                                  " and scopes ->> '*' != 'admin'"
                                  " order by username;", (f'{{{project_name}}}',))
        return [row[0] for row in rows.fetchall()]


def update_user_password(user: UpdateUser) -> RegisterVersionResponse:
    with pool.connection() as conn:
        conn.row_factory = tuple_row
        row = conn.execute("update users "
                           " set password = %s "
                           " where username = %s "
                           " returning id;",
                           (get_password_hash(user.password), user.username))
        log_message(f"Update user '{user.username}' password")
        return RegisterVersionResponse(inserted_id=str(row.fetchone()[0]), message="Password updated.")


def update_user_scopes(user: UpdateUser) -> RegisterVersionResponse:
    """Update scopes to the provided scopes regardless the existing scopes"""
    _user = get_user(user.username)
    with pool.connection() as conn:
        conn.row_factory = tuple_row
        # Check project: include special project "*"
        _check_scopes(user.scopes)
        row = conn.execute("update users "
                           " set scopes = %s "
                           " where username = %s "
                           " returning id;",
                           (Json(user.scopes), user.username))
        log_message(f"Update user '{user.username}' scopes to {user.scopes}")
        return RegisterVersionResponse(inserted_id=str(row.fetchone()[0]), message="Scopes updated")


def update_user(user: UpdateUser) -> ApplicationError | RegisterVersionResponse:
    _user = get_user(user.username)
    if _user is None:
        return ApplicationError(error=ApplicationErrorCode.user_not_found,
                                message=f"Check '{user.username}' user please.")

    current_response: RegisterVersionResponse = None

    log_message(f"Update user {user.username} with updated {user.scopes} scopes")
    if user.password is not None:
        current_response = update_user_password(user)

    if user.scopes is not None:
        if current_response is None:
            current_response = update_user_scopes(user)
        else:
            _additional_response = update_user_scopes(user)
            current_response.message = f"{current_response.message} {_additional_response.message}"

    return current_response


def self_update_user(username: str, new_password: str) -> RegisterVersionResponse:
    result = update_user_password(UpdateUser(username=username, password=new_password))
    revoke(username)
    return result
