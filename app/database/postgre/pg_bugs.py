# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from psycopg.rows import dict_row, tuple_row

from app.database.postgre.pg_versions import version_internal_id
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
                                 " where bg.id = %s"
                                 " and pj.alias = %s",
                                 (int(internal_id), provide(project_name))).fetchone()
    return BugTicketFull(**row)

async def db_update_bugs(project_name, internal_id, bug_ticket: UpdateBugTicket):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        bug_ticket_dict = bug_ticket.to_dict()
        current_bug = connection.execute("select criticality, status, version_id"
                                         " from bugs where id = %s;",
                                         (internal_id,)).fetchone()
        if "status" in bug_ticket_dict.keys() or "criticality" in bug_ticket_dict.keys():
            current_status_criticality = f"{current_bug['status']}_{current_bug['criticality']}"
            to_be_status_criticality = (
                f"{bug_ticket_dict['status'] if 'status' in bug_ticket_dict else current_bug['status']}"
                f"_{bug_ticket_dict['criticality'] if 'criticality' in bug_ticket_dict else current_bug['criticality']}")
            update_query = ("update versions"
                            f" set {current_status_criticality} = {current_status_criticality} - 1,"
                            f" {to_be_status_criticality} = {to_be_status_criticality} + 1"
                            f" where id = %s;")
            up_version = connection.execute(update_query,
                                            (current_bug["version_id"], ))
        to_set = ',\n '.join(f'{key} = %s' for key in bug_ticket_dict.keys() if key != "version")
        values = [value for key, value in bug_ticket_dict.items() if key != "version"]
        # TIPS: convert string version into internal id version
        if "version" in bug_ticket_dict:
            to_set = f"{to_set}, version_id = %s"
            values.append(await version_internal_id(project_name, bug_ticket_dict["version"]))

        values.append(internal_id)
        row = connection.execute(f"update bugs"
                                 f" set "
                                 f" {to_set}"
                                 f" where id = %s"
                                 f" returning id;",
                                 values)

    return await db_get_bug(project_name, internal_id)
        

async def version_bugs(project_name, version, side_version=None):
    # TODO to remove as it is a fake function
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
        update_query = (f"update versions as ve"
                        f" set {bug_ticket.status}_{bug_ticket.criticality}"
                        f" = {bug_ticket.status}_{bug_ticket.criticality} + 1"
                        f" from projects as pj"
                        f" where pj.alias = %s"
                        f" and pj.id = ve.project_id"
                        f" and ve.version = %s;")
        connection.execute(update_query, (provide(project_name), bug_ticket.version))
        return RegisterVersionResponse(inserted_id=row[0])
