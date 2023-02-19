# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List

from psycopg.rows import dict_row

from app.database.postgre.pg_projects import get_projects
from app.database.utils.transitions import version_transition
from app.schema.project_schema import Bugs, Statistics, UpdateVersion, Version
from app.utils.pgdb import pool
from app.utils.project_alias import contains, provide, register


async def get_version(project_name: str, version: str):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute("select * "
                                 "from versions as ve"
                                 "join projects as pjt on pjt.id = ve.project_id "
                                 "where pjt.alias = %s "
                                 "and ve.version = %s;",
                                 (provide(project_name), version)).fetchone()
        if row is None:
            raise Exception("Version not found")

        stats = Statistics(open=row["open"],
                           cancelled=row["cancelled"],
                           blocked=row["blocked"],
                           in_progress=row["in_progress"],
                           done=row["done"])
        bugs = Bugs(open_blocking=row["open_blocking"],
                    open_major=row["open_blocking"],
                    open_minor=row["open_minor"],
                    closed_blocking=row["closed_blocking"],
                    closed_major=row["closed_major"],
                    closed_minor=row["closed_minor"])
        return Version(version=version,
                       created=row["created"],
                       updated=row["updated"],
                       started=row["started"],
                       end_forecast=row["end_forecast"],
                       status=row["status"],
                       statistics=stats,
                       bugs=bugs)


async def get_versions(project_name: str, exclude_archived: bool = False) -> list:
    with pool.connection() as connection:
        if exclude_archived:
            return list(connection.execute("select version "
                                           "from versions as ve "
                                           "join projects as pjt on pjt.id = ve.project_id"
                                           "where pjt.alias = %s"
                                           "and ve.status != 'archived';",
                                           (provide(project_name, ))).fetchall())
        return list(connection.execute("select version "
                                       "from versions as ve "
                                       "join projects as pjt on pjt.id = ve.project_id"
                                       "where pjt.alias = %s;",
                                       (provide(project_name, ))).fetchall())


async def get_project_versions(project_name: str, exclude_archived: bool = False) -> List[Version]:
    result = []
    with pool.connection() as connection:
        connection.row_factory = dict_row
        if exclude_archived:
            rows = connection.execute("select * "
                                 "from versions as ve"
                                 "join projects as pjt on pjt.id = ve.project_id "
                                 "where pjt.alias = %s "
                                 "and ve.status != 'archived';",
                                 (provide(project_name), )).fetchall()
        else:
            rows = connection.execute("select * "
                                 "from versions as ve"
                                 "join projects as pjt on pjt.id = ve.project_id "
                                 "where pjt.alias = %s ;",
                                 (provide(project_name), )).fetchall()
        for row in rows:
            stats = Statistics(open=row["open"],
                               cancelled=row["cancelled"],
                               blocked=row["blocked"],
                               in_progress=row["in_progress"],
                               done=row["done"])
            bugs = Bugs(open_blocking=row["open_blocking"],
                        open_major=row["open_blocking"],
                        open_minor=row["open_minor"],
                        closed_blocking=row["closed_blocking"],
                        closed_major=row["closed_major"],
                        closed_minor=row["closed_minor"])
            result.append(Version(version=row["version"],
                           created=row["created"],
                           updated=row["updated"],
                           started=row["started"],
                           end_forecast=row["end_forecast"],
                           status=row["status"],
                           statistics=stats,
                           bugs=bugs))
    return result

async def update_version_status(project_name: str, version: str, to_be_status: str):
    _version = await get_version(project_name, version)
    version_transition(_version["status"], to_be_status)
    with pool.connection() as connection:
        connection.execute("update versions ve "
                           "set ve.status = %s, "
                           "ve.updated = %s "
                           "from projects pjt "
                           "where pjt.alias = %s "
                           "and pjt.id = ve.project_id "
                           "and version = %s;",
                           (to_be_status, datetime.now(), provide(project_name), version))
    return await get_version(project_name, version)


async def update_version_data(project_name: str, version: str, body: UpdateVersion):
    if "status" in body:
        await update_version_status(project_name, version, body["status"])
    with pool.connection() as connection:
        if "started" in body and "end_forecast" in body:
            connection.execute("update versions ve "
                               "set ve.started = %s,"
                               "ve.end_forecast = %s, "
                               "ve.updated = %s "
                               "from projects pjt "
                               "where pjt.alias = %s "
                               "and pjt.id = ve.project_id "
                               "and version = %s;",
                               (body.started,
                                body.end_forecast,
                                datetime.now(),
                                provide(project_name),
                                version))
        elif "started" in body and "end_forecast" not in body:
            connection.execute("update versions ve "
                               "set ve.started = %s,"
                               "ve.updated = %s "
                               "from projects pjt "
                               "where pjt.alias = %s "
                               "and pjt.id = ve.project_id "
                               "and version = %s;",
                               (body.started,
                                datetime.now(),
                                provide(project_name),
                                version))
        else:
            connection.execute("update versions ve "
                               "set ve.end_forecast = %s, "
                               "ve.updated = %s "
                               "from projects pjt "
                               "where pjt.alias = %s "
                               "and pjt.id = ve.project_id "
                               "and version = %s;",
                               (body.end_forecast,
                                datetime.now(),
                                provide(project_name),
                                version))

    return await get_version(project_name, version)

async def dashboard():
    projects = await get_projects()
    result = []
    for project in projects:
        project_versions = await get_project_versions(project, True)
        result.extend({"name": project,
                       "alias": provide(project),
                       **version} for version in project_versions)
    return result
