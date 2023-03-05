# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import (List, Optional)

from psycopg import (DatabaseError, IntegrityError)
from psycopg.rows import dict_row, tuple_row

from app.app_exception import (DuplicateProject, DuplicateVersion, ProjectNameInvalid)
from app.schema.project_enum import DashCollection

from app.schema.project_schema import RegisterVersion, RegisterVersionResponse
from app.utils.pgdb import pool
from app.utils.project_alias import contains, provide, register


async def register_project(project_name: str):
    if len(project_name) > 63:
        raise ProjectNameInvalid("Project name must be strictly less than 64 character")
    # Add check that project name does not contain \ / $ symbols raise an error
    forbidden_char = ["\\", "/", "$"]
    if any(char in project_name for char in forbidden_char):
        raise ProjectNameInvalid("Project name must not be contains \\ / $ characters")
    if contains(project_name):
        raise DuplicateProject(f"Project name '{project_name}' "
                               f"already exists. Please update the name "
                               f"so that project can be registered.")
    register(project_name)
    with pool.connection() as connection:
        connection.execute("insert into projects (name, alias) values (%s, %s);",
                           (project_name.casefold(), provide(project_name)))

    return project_name

async def registered_projects():
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return [item[0] for item in connection.execute("select name from projects;").fetchall()]


async def get_projects(skip: int = 0, limit: int = 10):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        # The query returns null instead of 0 value.
        # TODO: check the query
        rows = connection.execute(
            "select pj.name as name,"
            " (select coalesce(count(v1.id),0) "
            " from versions as v1 "
            " where v1.project_id = pj.id "
            " group by v1.project_id, v1.status "
            " having v1.status = 'recorded') as future,"
            " (select coalesce(count(v2.id),0) "
            " from versions as v2 "
            " where v2.project_id = pj.id "
            " group by v2.project_id, v2.status "
            " having v2.status = 'done') as archived,"
            " (select coalesce(count(v3.id),0) "
            " from versions as v3 "
            " where v3.project_id = pj.id "
            " group by v3.project_id, v3.status "
            " having v3.status not in ('recorded', 'done')) as current"
            " from projects as pj"
            " order by pj.name "
            " limit %s offset %s;", (limit, skip))
        return list(rows.fetchall())


async def create_project_version(project_name: str, project: RegisterVersion):
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            row = connection.execute("insert into versions (project_id, version) "
                               " select id, %s from projects where alias = %s"
                               " returning id;",
                               (project.version, provide(project_name))).fetchone()

            return RegisterVersionResponse(inserted_id=row["id"])
    except IntegrityError as ie:
        raise DuplicateVersion(', '.join(ie.args)) from ie
    except DatabaseError as de:
        raise DuplicateVersion(', '.join(de.args)) from de

async def get_project(project_name: str, sections: Optional[List[str]]):
    result = {"name": project_name.casefold()}
    with pool.connection() as connection:
        connection.row_factory = dict_row
        _sections = [sec.casefold() for sec in sections] if sections is not None else []
        result = {"name": project_name}
        if DashCollection.CURRENT.value in _sections or not _sections:
            current = connection.execute("select ve.version, ve.created, ve.updated, ve.started, ve.end_forecast, ve.status"
                                         " from versions as ve"
                                         " join projects as pj on pj.id = ve.project_id"
                                         " where ve.status not in ('recorded', 'done')"
                                         " and pj.alias = %s;", (provide(project_name),))
            result[DashCollection.CURRENT.value] = list(current.fetchall())
        if DashCollection.FUTURE.value in _sections or not _sections:
            future = connection.execute("select ve.version, ve.created, ve.updated, ve.started, ve.end_forecast, ve.status"
                                         " from versions as ve"
                                         " join projects as pj on pj.id = ve.project_id"
                                         " where ve.status = 'recorded'"
                                         " and pj.alias = %s;", (provide(project_name),))
            result[DashCollection.FUTURE.value] = list(future.fetchall())
        if DashCollection.ARCHIVED.value in _sections or not _sections:
            archived = connection.execute("select ve.version, ve.created, ve.updated, ve.started, ve.end_forecast, ve.status"
                                         " from versions as ve"
                                         " join projects as pj on pj.id = ve.project_id"
                                         " where ve.status = 'done'"
                                         " and pj.alias = %s;", (provide(project_name),))
            result[DashCollection.ARCHIVED.value] = list(archived.fetchall())
    return result

async def set_index(project_name):
    # Fake temporary function
    # TODO: Remove
    pass
