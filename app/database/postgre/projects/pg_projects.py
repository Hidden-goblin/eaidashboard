# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Tuple

from psycopg import DatabaseError, IntegrityError
from psycopg.rows import dict_row, tuple_row

from app.app_exception import DuplicateProject, ProjectNameInvalid
from app.database.postgre.pg_utils import _compile
from app.database.postgre.projects.projects_query import (
    build_count_projects_query,
    build_create_project_version_query,
    build_get_project_archived_versions_query,
    build_get_project_current_versions_query,
    build_get_project_future_versions_query,
    build_get_projects_query,
    build_register_project_query,
    build_registered_projects_query,
)
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.project_enum import DashCollection
from app.schema.project_schema import Project, RegisterVersion, RegisterVersionResponse, TicketProject
from app.schema.ticket_schema import TicketVersion
from app.utils.pgdb import pool
from app.utils.project_alias import contains, provide, register


def validate_project_name(project_name: str) -> None:
    if len(project_name) > 63:
        raise ProjectNameInvalid("Project name must be strictly less than 64 character")
    # Add check that project name does not contain \ / $ symbols raise an error
    forbidden_char = ["\\", "/", "$"]
    if any(char in project_name for char in forbidden_char):
        raise ProjectNameInvalid("Project name must not contain \\ / $ characters")
    if project_name == "*":
        raise ProjectNameInvalid("Project name must be different from '*' special project")
    if contains(project_name):
        raise DuplicateProject(
            f"Project name '{project_name}' already exists. Please update the name so that project can be registered."
        )


async def register_project(project_name: str) -> str:
    validate_project_name(project_name)
    register(project_name)
    query, params = _compile(build_register_project_query(project_name, provide(project_name)))
    with pool.connection() as connection:
        connection.execute(query, params)

    return project_name


async def registered_projects() -> List[str]:
    query, params = _compile(build_registered_projects_query())
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return [item[0] for item in connection.execute(query, params).fetchall()]


async def get_projects(
    skip: int = 0,
    limit: int = 10,
) -> Tuple[List[Project], int]:
    query, params = _compile(build_get_projects_query(skip=skip, limit=limit))
    count_query, count_params = _compile(build_count_projects_query())
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(query, params)
        count = connection.execute(count_query, count_params)
        return list(rows.fetchall()), int(count.fetchone()["total"])


async def create_project_version(
    project_name: str,
    project: RegisterVersion,
) -> RegisterVersionResponse | ApplicationError:
    try:
        query, params = _compile(build_create_project_version_query(provide(project_name), project.version))
        with pool.connection() as connection:
            connection.row_factory = dict_row
            row = connection.execute(query, params).fetchone()

            result = RegisterVersionResponse(
                inserted_id=row["id"],
            )
    except IntegrityError as ie:
        result = ApplicationError(
            error=ApplicationErrorCode.duplicate_element,
            message=", ".join(ie.args),
        )
    except DatabaseError as de:
        result = ApplicationError(
            error=ApplicationErrorCode.duplicate_element,
            message=", ".join(de.args),
        )

    return result


async def get_project(
    project_name: str,
    sections: Optional[List[str]],
) -> TicketProject:
    result = {"name": project_name.casefold()}
    with pool.connection() as connection:
        connection.row_factory = dict_row
        _sections = [sec.casefold() for sec in sections] if sections is not None else []
        result = {
            "name": project_name,
        }
        project_alias = provide(project_name)
        if DashCollection.CURRENT.value in _sections or not _sections:
            query, params = _compile(build_get_project_current_versions_query(project_alias))
            current = connection.execute(query, params)
            result[DashCollection.CURRENT.value] = [TicketVersion(**cur) for cur in current.fetchall()]
        if DashCollection.FUTURE.value in _sections or not _sections:
            query, params = _compile(build_get_project_future_versions_query(project_alias))
            future = connection.execute(query, params)
            result[DashCollection.FUTURE.value] = [TicketVersion(**fut) for fut in future.fetchall()]
        if DashCollection.ARCHIVED.value in _sections or not _sections:
            query, params = _compile(build_get_project_archived_versions_query(project_alias))
            archived = connection.execute(query, params)
            result[DashCollection.ARCHIVED.value] = [TicketVersion(**arch) for arch in archived.fetchall()]
    return TicketProject(**result)
