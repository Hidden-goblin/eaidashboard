# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import (List, Optional)

from psycopg import (DatabaseError, IntegrityError)
from psycopg.rows import dict_row

from app.app_exception import (DuplicateProject, DuplicateVersion, ProjectNameInvalid)
from app.schema.project_schema import RegisterVersion
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
        connection.execute("insert into projects (name, alias) value (%s, %s);",
                           (project_name.casefold(), provide(project_name)))


async def registered_projects():
    with pool.connection() as connection:
        return list(connection.execute("select name from projects;").fetchall())


async def get_projects(skip: int = 0, limit: int = 10):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            "select pj.name as name,"
            " (select count(v1.id) "
            " from versions as v1 "
            " where v1.project_id = pj.id "
            " group by v1.project_id, v1.status "
            " having v1.status = 'open') as future,"
            " (select count(v2.id) "
            " from versions as v2 "
            " where v2.project_id = pj.id "
            " group by v2.project_id, v2.status "
            " having v2.status = 'done') as archived,"
            " (select count(v3.id) "
            " from versions as v3 "
            " where v3.project_id = pj.id "
            " group by v3.project_id, v3.status "
            " having v3.status not in ('open', 'done')) as current"
            " from projects as pj"
            " order by pj.name "
            " limit %s offset %s;", (limit, skip))
        return list(rows.fetchall())


async def create_project_version(project_name: str, project: RegisterVersion):
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            connection.execute("insert into versions (project_id, version) "
                               "select id, %s from projects where alias = %s;",
                               (project.version, provide(project_name)))
    except IntegrityError as ie:
        raise DuplicateVersion(', '.join(ie.args)) from ie
    except DatabaseError as de:
        raise DuplicateVersion(', '.join(de.args)) from de

async def get_project(project_name: str, sections: Optional[List[str]]):
    result = {"name": project_name.casefold()}
    with pool.connection() as connection:
        connection.row_factory = dict_row

    return result

