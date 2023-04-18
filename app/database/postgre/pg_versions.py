# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List

from psycopg.rows import dict_row, tuple_row

from app.app_exception import TicketNotFound, VersionNotFound
from app.database.postgre.pg_projects import get_projects
from app.database.utils.transitions import version_transition
from app.schema.bugs_schema import Bugs, UpdateVersion
from app.schema.project_schema import Statistics
from app.schema.status_enum import TicketType
from app.schema.versions_schema import Version
from app.utils.log_management import log_message
from app.utils.pgdb import pool
from app.utils.project_alias import provide


async def version_exists(project_name: str, version: str) -> bool:
    with pool.connection() as connection:
        row = connection.execute("select ve.id "
                                 " from versions as ve "
                                 " join projects as pjt on pjt.id = ve.project_id "
                                 " where pjt.alias = %s "
                                 " and ve.version = %s;",
                                 (provide(project_name), version)).fetchone()
        return row is not None


async def get_version(project_name: str, version: str) -> Version:
    """Assuming that project_name and version exists
    :raise TypeError: 'NoneType' object is not subscriptable"""
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute("select * "
                                 " from versions as ve"
                                 " join projects as pjt on pjt.id = ve.project_id "
                                 " where pjt.alias = %s "
                                 " and ve.version = %s;",
                                 (provide(project_name), version)).fetchone()

        stats = Statistics(open=row["open"],
                           cancelled=row["cancelled"],
                           blocked=row["blocked"],
                           in_progress=row["in_progress"],
                           done=row["done"])
        bugs = Bugs(open_blocking=row["open_blocking"],
                    open_major=row["open_major"],
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
        connection.row_factory = tuple_row
        if exclude_archived:
            return [row[0] for row in connection.execute("select version "
                                                         " from versions as ve "
                                                         " join projects as pjt on pjt.id = "
                                                         "ve.project_id"
                                                         " where pjt.alias = %s"
                                                         " and ve.status != 'archived';",
                                                         (provide(project_name),)).fetchall()]
        return [row[0] for row in connection.execute("select version "
                                                     " from versions as ve "
                                                     " join projects as pjt on pjt.id = "
                                                     "ve.project_id"
                                                     " where pjt.alias = %s;",
                                                     (provide(project_name),)).fetchall()]


async def get_project_versions(project_name: str, exclude_archived: bool = False) -> List[Version]:
    result = []
    with pool.connection() as connection:
        connection.row_factory = dict_row
        if exclude_archived:
            rows = connection.execute("select * "
                                      " from versions as ve"
                                      " join projects as pjt on pjt.id = ve.project_id "
                                      " where pjt.alias = %s "
                                      " and ve.status != 'archived';",
                                      (provide(project_name),)).fetchall()
        else:
            rows = connection.execute("select * "
                                      " from versions as ve"
                                      " join projects as pjt on pjt.id = ve.project_id "
                                      " where pjt.alias = %s ;",
                                      (provide(project_name),)).fetchall()
        for row in rows:
            stats = Statistics(open=row["open"],
                               cancelled=row["cancelled"],
                               blocked=row["blocked"],
                               in_progress=row["in_progress"],
                               done=row["done"])
            bugs = Bugs(open_blocking=row["open_blocking"],
                        open_major=row["open_major"],
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


async def update_version_data(project_name: str, version: str, body: UpdateVersion):
    updates = {}
    if body.started is not None:
        updates["started"] = datetime.strptime(body.started, "%Y-%m-%d")
    if body.end_forecast is not None:
        updates["end_forecast"] = datetime.strptime(body.end_forecast, "%Y-%m-%d")
    if body.status is not None:
        _version = await get_version(project_name, version)
        version_transition(_version["status"], body.status)
        updates["status"] = body.status
    if updates:
        updates["updated"] = datetime.now()
        with pool.connection() as connection:
            query = ("update versions ve"
                     " set " + ", ".join(f"{k} = %s" for k in updates) +
                     " from projects pjt"
                     " where pjt.alias = %s"
                     " and pjt.id = ve.project_id"
                     " and version = %s")
            log_message(query)
            data = [*updates.values(), provide(project_name), version]
            connection.execute(query, data)

    return await get_version(project_name, version)


async def dashboard():
    projects = await get_projects()
    result = []
    for project in projects:
        project_versions = await get_project_versions(project["name"], True)
        result.extend({"name": project["name"],
                       "alias": provide(project["name"]),
                       **version.dict()} for version in project_versions)
    return result


async def update_status_for_ticket_in_version(project_name,
                                              version,
                                              ticket_reference,
                                              updated_status):
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        current_ticket = connection.execute("select tk.status, tk.current_version"
                                            " from tickets as tk"
                                            " join versions as ve on tk.current_version = ve.id"
                                            " join projects as pj on pj.id = ve.project_id"
                                            " where pj.alias = %s"
                                            " and ve.version = %s"
                                            " and tk.reference = %s;",
                                            (provide(project_name),
                                             version,
                                             ticket_reference)).fetchone()
        if current_ticket is None:
            raise TicketNotFound(
                f"Ticket '{ticket_reference}' does not exist in project '{project_name}'"
                f" version '{version}'")
        if current_ticket[0] != updated_status:
            row = connection.execute("update versions"
                                     f" set {current_ticket[0]} = {current_ticket[0]} -1,"
                                     f" {updated_status} = {updated_status} + 1"
                                     f" where id = %s", (current_ticket[1],))
            log_message(row)
        return True


async def version_internal_id(project_name: str, version: str) -> int:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute("select ve.id"
                                  " from versions as ve"
                                  " join projects as pj on pj.id = ve.project_id"
                                  " where pj.alias = %s"
                                  " and ve.version = %s;",
                                  (provide(project_name), version)).fetchone()[0]


async def refresh_version_stats(project_name: str = None, version: str = None):
    # TODO: Limit to project-version in general except for future cron task
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        query_version = "select ve.id from versions as ve {join} {where} {filter};"
        query_join = ""
        query_filter = ""
        query_data = []
        if project_name is not None:
            query_join = "join projects as pj on pj.id = ve.project_id"
            query_filter = "pj.alias = %s"
            query_data.append(provide(project_name))
        if version is not None:
            query_filter = f"{query_filter} {'and' if query_filter else ''} ve.version = %s"
            query_data.append(version)
        full_query = query_version.format(join=query_join,
                                          where="where" if query_filter else "",
                                          filter=query_filter)
        versions = connection.execute(full_query, query_data).fetchall()

        query = ("select count(tk.id)"
                 " from tickets as tk"
                 " where tk.current_version = %s"
                 " and tk.status = %s;")
        for version in versions:
            count_open = connection.execute(query,
                                            (version[0], TicketType.OPEN.value)).fetchone()[0]
            count_in_progress = connection.execute(query,
                                                   (version[0],
                                                    TicketType.IN_PROGRESS.value)).fetchone()[0]
            count_blocked = connection.execute(query,
                                               (version[0], TicketType.BLOCKED.value)).fetchone()[0]
            count_cancelled = connection.execute(query,
                                                 (version[0],
                                                  TicketType.CANCELLED.value)).fetchone()[0]
            count_done = connection.execute(query,
                                            (version[0], TicketType.DONE.value)).fetchone()[0]
            connection.execute("update versions"
                               " set open = %s,"
                               " in_progress = %s,"
                               " blocked = %s,"
                               " cancelled = %s,"
                               " done = %s"
                               " where id = %s;", (count_open,
                                                   count_in_progress,
                                                   count_blocked,
                                                   count_cancelled,
                                                   count_done,
                                                   version[0]))
            connection.commit()
