# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from psycopg.rows import dict_row, tuple_row

from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.bugs_schema import BugTicket, UpdateBugTicket, BugTicketFull
from app.schema.project_schema import RegisterVersionResponse
from app.utils.pgdb import pool
from app.utils.project_alias import provide


async def compute_bugs(project_name):
    pass


async def get_bugs(project_name: str,
                   status: Optional[BugStatusEnum] = None,
                   criticality: Optional[BugCriticalityEnum] = None,
                   version: str = None):
    query = ("select bg.id as internal_id,"
             " bg.title,"
             " bg.url,"
             " bg.description,"
             " ve.version as version,"
             " bg.criticality,"
             " bg.status,"
             " bg.created,"
             " bg.updated"
             " from bugs as bg"
             " join projects as pj on pj.id = bg.project_id"
             " join versions as ve on ve.id = bg.version_id")

    query_filter = ["pj.alias = %s"]
    data = [provide(project_name)]
    if version is not None:
        query_filter.append("ve.version = %s")
        data.append(version)
    if status is not None:
        query_filter.append("bg.status = %s")
        data.append(status)
    if criticality is not None:
        query_filter.append("bg.criticality = %s")
        data.append(criticality.value)

    final_query = f"{query} where {' and '.join(query_filter)};"
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(final_query, data).fetchall()

        return [BugTicketFull(**row) for row in rows]


async def db_get_bug(project_name: str,
                     internal_id: str) -> BugTicketFull:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute("select bg.id as internal_id,"
                                 " bg.title,"
                                 " bg.url,"
                                 " bg.description,"
                                 " ve.version as version,"
                                 " bg.criticality,"
                                 " bg.status,"
                                 " bg.created,"
                                 " bg.updated"
                                 " from bugs as bg"
                                 " join projects as pj on pj.id = bg.project_id"
                                 " join versions as ve on ve.id = bg.version_id"
                                 " where bg.id = %"
                                 " and pj.alias = %s",
                                 (int(internal_id), provide(project_name))).fetchone()
    return BugTicketFull(**row)

async def db_update_bugs(project_name, internal_id, bug_ticket: UpdateBugTicket):
    pass

async def version_bugs(project_name, version, side_version=None):
    pass


async def insert_bug(project_name: str, bug_ticket: BugTicket) -> RegisterVersionResponse:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        row = connection.execute(
            "insert into bugs (title, url, description, project_id, version_id, criticality, "
            "status)"
            " select %s, %s, %s, pj.id, ve.id, %s, %s"
            " from versions as ve"
            " join projects as pj on pj.id = ve.project_id"
            " where ve.version = %s"
            " and pj.alias = %s"
            " returning bugs.id;",
            (bug_ticket.title,
             bug_ticket.url,
             bug_ticket.description,
             bug_ticket.criticality,
             BugStatusEnum.open.value,
             bug_ticket.version,
             provide(project_name))).fetchone()
        return RegisterVersionResponse(inserted_id=row[0])
