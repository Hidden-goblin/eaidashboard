# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Tuple

from psycopg import DatabaseError, IntegrityError
from psycopg.rows import dict_row, tuple_row

from app.app_exception import DuplicateProject, ProjectNameInvalid
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.project_enum import DashCollection
from app.schema.project_schema import Project, RegisterVersion, RegisterVersionResponse, TicketProject
from app.schema.ticket_schema import TicketVersion
from app.utils.pgdb import pool
from app.utils.project_alias import contains, provide, register


async def register_project(project_name: str) -> str:
    if len(project_name) > 63:
        raise ProjectNameInvalid("Project name must be strictly less than 64 character")
    # Add check that project name does not contain \ / $ symbols raise an error
    forbidden_char = ["\\", "/", "$"]
    if any(char in project_name for char in forbidden_char):
        raise ProjectNameInvalid("Project name must not contain \\ / $ characters")
    if project_name == "*":
        raise ProjectNameInvalid("Project name must be different from '*' special project")
    if contains(project_name):
        raise DuplicateProject(f"Project name '{project_name}' "
                               f"already exists. Please update the name "
                               f"so that project can be registered.")
    register(project_name)
    with pool.connection() as connection:
        connection.execute("insert into projects (name, alias) values (%s, %s);",
                           (project_name.casefold(), provide(project_name)))

    return project_name


async def registered_projects() -> List[str]:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return [item[0] for item in connection.execute("select name from projects;").fetchall()]


async def get_projects(skip: int = 0, limit: int = 10) -> Tuple[List[Project], int]:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        # The query returns null instead of 0 value.
        # TODO: check the query
        rows = connection.execute(
            "select pj.name as name,"
            " coalesce((select count(v1.id) "
            " from versions as v1 "
            " where v1.project_id = pj.id "
            " group by v1.project_id, v1.status "
            " having v1.status = 'recorded'), 0) as future,"
            " coalesce((select count(v2.id) "
            " from versions as v2 "
            " where v2.project_id = pj.id "
            " group by v2.project_id, v2.status "
            " having v2.status = 'done'),0) as archived,"
            " coalesce((select count(v3.id) "
            " from versions as v3 "
            " where v3.project_id = pj.id"
            " and v3.status != 'recorded'"
            " and v3.status != 'done'"
            " group by v3.project_id),0) as current"
            " from projects as pj"
            " order by pj.name "
            " limit %s offset %s;", (limit, skip))
        count = connection.execute("select count(distinct id) as total from projects;")
        return list(rows.fetchall()), int(count.fetchone()['total'])


async def create_project_version(project_name: str,
                                 project: RegisterVersion) -> RegisterVersionResponse | \
                                                              ApplicationError:
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            row = connection.execute("insert into versions (project_id, version) "
                                     " select id, %s from projects where alias = %s"
                                     " returning id;",
                                     (project.version, provide(project_name))).fetchone()

            result = RegisterVersionResponse(inserted_id=row["id"])
    except IntegrityError as ie:
        result = ApplicationError(error=ApplicationErrorCode.duplicate_element,
                                  message=', '.join(ie.args))
    except DatabaseError as de:
        result = ApplicationError(error=ApplicationErrorCode.duplicate_element,
                                  message=', '.join(de.args))

    return result


async def get_project(project_name: str,
                      sections: Optional[List[str]]) -> TicketProject:
    result = {"name": project_name.casefold()}
    with pool.connection() as connection:
        connection.row_factory = dict_row
        _sections = [sec.casefold() for sec in sections] if sections is not None else []
        result = {"name": project_name}
        if DashCollection.CURRENT.value in _sections or not _sections:
            current = connection.execute(
                "select ve.version, ve.created, ve.updated, ve.started, ve.end_forecast, ve.status"
                " from versions as ve"
                " join projects as pj on pj.id = ve.project_id"
                " where ve.status not in ('recorded', 'archived')"
                " and pj.alias = %s;", (provide(project_name),))
            result[DashCollection.CURRENT.value] = [TicketVersion(**cur) for cur in current.fetchall()]
        if DashCollection.FUTURE.value in _sections or not _sections:
            future = connection.execute(
                "select ve.version, ve.created, ve.updated, ve.started, ve.end_forecast, ve.status"
                " from versions as ve"
                " join projects as pj on pj.id = ve.project_id"
                " where ve.status = 'recorded'"
                " and pj.alias = %s;", (provide(project_name),))
            result[DashCollection.FUTURE.value] = [TicketVersion(**fut) for fut in future.fetchall()]
        if DashCollection.ARCHIVED.value in _sections or not _sections:
            archived = connection.execute(
                "select ve.version, ve.created, ve.updated, ve.started, ve.end_forecast, ve.status"
                " from versions as ve"
                " join projects as pj on pj.id = ve.project_id"
                " where ve.status = 'archived'"
                " and pj.alias = %s;", (provide(project_name),))
            result[DashCollection.ARCHIVED.value] = [TicketVersion(**arch) for arch in archived.fetchall()]
    return TicketProject(**result)
