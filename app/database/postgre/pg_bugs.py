# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from logging import getLogger
from typing import List, Optional, Tuple

from psycopg.rows import dict_row, tuple_row

from app.database.postgre.pg_versions import version_internal_id
from app.database.redis.rs_file_management import rs_invalidate_file
from app.database.utils.transitions import bug_authorized_transition, version_transition
from app.schema.bugs_schema import BugTicket, BugTicketFull, CampaignTicketScenario, UpdateBugTicket
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.project_schema import RegisterVersionResponse
from app.schema.status_enum import BugStatusEnum
from app.utils.pgdb import pool
from app.utils.project_alias import provide

logger = getLogger(__name__)


async def get_bugs(project_name: str,
                   status: Optional[List[BugStatusEnum]] = None,
                   criticality: Optional[BugCriticalityEnum] = None,
                   version: str = None,
                   limit: int = 100,
                   skip: int = 0,) -> Tuple[List[BugTicketFull], int]:
    query = ("select bg.id as internal_id,"
             " bg.title,"
             " bg.url,"
             " bg.description,"
             " ve.version as version,"
             " bg.criticality,"
             " bg.status,"
             " bg.created,"
             " bg.updated,"
             " json_agg("
             " 	json_strip_nulls(json_build_object("
             " 'occurrence', bugs_issues.occurrence,"
             " 'ticket_reference', bugs_issues.ticket_reference,"
             " 'scenario_tech_id', bugs_issues.scenario_id)"
             "))  as related_to"
             " from bugs as bg"
             " join projects as pj on pj.id = bg.project_id"
             " join versions as ve on ve.id = bg.version_id"
             " left join bugs_issues on bg.id = bugs_issues.bug_id"
             )
    count_query = ("select count(bg.id) as total"
                   " from bugs as bg"
                   " join projects as pj on pj.id = bg.project_id"
                   " join versions as ve on ve.id = bg.version_id")
    query_filter = ["pj.alias = %s"]
    data = [provide(project_name)]
    if version is not None:
        query_filter.append("ve.version = %s")
        data.append(version)
    if status is not None:
        query_filter.append("bg.status = ANY(%s)")
        data.append([str(stat) for stat in status])
    if criticality is not None:
        query_filter.append("bg.criticality = %s")
        data.append(criticality.value)

    final_query = (f"{query} where {' and '.join(query_filter)}"
                   f" group by bg.id, ve.version"
                   f" order by ve.version, bg.id"
                   f" limit %s offset %s;")
    final_count_query = f"{count_query}  where {' and '.join(query_filter)};"

    data.extend((limit, skip))
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(final_query, data).fetchall()
        # Remove the last two elements from the list, they are not needed
        data.pop()
        data.pop()
        count = connection.execute(final_count_query, data).fetchone()["total"]

        return [BugTicketFull(**row) for row in rows], count


async def db_get_bug(project_name: str,
                     internal_id: str,) -> BugTicketFull | ApplicationError:
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
                                 " bg.updated,"
                                 " json_agg("
                                 " 	json_strip_nulls(json_build_object("
                                 " 'occurrence', bugs_issues.occurrence,"
                                 " 'ticket_reference', bugs_issues.ticket_reference,"
                                 " 'scenario_tech_id', bugs_issues.scenario_id)"
                                 "))  as related_to"
                                 " from bugs as bg"
                                 " join projects as pj on pj.id = bg.project_id"
                                 " join versions as ve on ve.id = bg.version_id"
                                 " left join bugs_issues on bg.id = bugs_issues.bug_id"
                                 " where bg.id = %s"
                                 " and pj.alias = %s"
                                 " group by bg.id, ve.version;",
                                 (int(internal_id), provide(project_name))).fetchone()
    return BugTicketFull(**row) if row else ApplicationError(
        error=ApplicationErrorCode.bug_not_found,
        message=f"Bug '{internal_id}' is not found."
    )


def db_bug_linked_scenario(bug_internal_id: int = None) -> List[CampaignTicketScenario | None]:
    if bug_internal_id is None:
        return []
    query = ("select occurrence, ticket_reference, scenario_id as scenario_tech_id"
             " from bugs_issues"
             " where bug_id = %s;")
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(query, (bug_internal_id,))
        return [CampaignTicketScenario(**row) for row in rows]


def __update_bug_status(
        current_bug: BugTicketFull, bug_ticket: UpdateBugTicket,) -> None:
    if (bug_ticket.status is not None
            or bug_ticket.criticality is not None):
        open_close_collapse = {BugStatusEnum.open: BugStatusEnum.open.value,
                               BugStatusEnum.fix_ready: BugStatusEnum.open.value,
                               BugStatusEnum.closed: BugStatusEnum.closed.value,
                               BugStatusEnum.closed_not_a_defect: BugStatusEnum.closed.value}

        current_status_criticality = (f"{open_close_collapse[current_bug.status]}_"
                                      f"{current_bug.criticality}")
        to_be_status_criticality = (
            f"{open_close_collapse[bug_ticket.to_dict().get('status', current_bug['status'])]}"
            f"_{bug_ticket.to_dict().get('criticality', current_bug['criticality'])}")
        if current_status_criticality != to_be_status_criticality:
            update_query = (
                "update versions"
                f" set {current_status_criticality} = {current_status_criticality} - 1,"
                f" {to_be_status_criticality} = {to_be_status_criticality} + 1"
                f" where id = %s;")
            with pool.connection() as connection:
                connection.row_factory = dict_row
                up_version = connection.execute(update_query,
                                                (current_bug["version_id"],))
                logger.info(up_version.statusmessage)


async def db_update_bugs(project_name: str,
                         internal_id: str,
                         bug_ticket: UpdateBugTicket,) -> BugTicketFull | ApplicationError:
    bug_ticket_dict = bug_ticket.to_dict()
    current_bug: BugTicketFull = await db_get_bug(project_name, internal_id)
    if isinstance(current_bug, ApplicationError):
        return current_bug

    # Status update must follow transition pattern
    if "status" in bug_ticket_dict.keys():
        version_transition(current_bug["status"],
                           str(bug_ticket_dict['status']),
                           BugStatusEnum,
                           bug_authorized_transition)
    __update_bug_status(current_bug, bug_ticket)
    # All fields update from bug_ticket
    to_set = ',\n '.join(f'{key} = %s' for key in bug_ticket.to_sql().keys() if key != "version")
    values = [value for key, value in bug_ticket.to_sql().items() if key != "version"]
    version = current_bug.version
    # TIPS: convert string version into internal id version
    if "version" in bug_ticket_dict:
        version = bug_ticket_dict["version"]
        to_set = f"{to_set}, version_id = %s"
        version_id = await version_internal_id(project_name, bug_ticket_dict["version"])
        if isinstance(version_id, ApplicationError):
            return version_id
        values.append(version_id)
        # SPEC: Invalidate all files of the future version
        await rs_invalidate_file(f"file:{project_name}:{bug_ticket.version}:*")
        # ToDo: update statuses from past version to current version

    values.append(internal_id)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(f"update bugs"
                                 f" set "
                                 f" {to_set}"
                                 f" where id = %s"
                                 f" returning id;",
                                 values)
        logger.info(row.statusmessage)
    # Link bug to scenario
    if bug_ticket.related_to:
        await make_link_to_scenario(project_name, version, bug_ticket.related_to, int(internal_id))
    # Unlink bug to scenario
    if bug_ticket.unlink_scenario:
        await unlink_from_scenario(project_name, version, bug_ticket.unlink_scenario, int(internal_id))
    # SPEC invalidate all files of the current version
    await rs_invalidate_file(f"file:{project_name}:{current_bug.version}:*")
    return await db_get_bug(project_name, internal_id)


async def make_link_to_scenario(project_name: str,
                                version: str,
                                related_to: List[CampaignTicketScenario],
                                bug_id: int,) -> int:
    # validate existence

    # Insert
    query = ("insert into bugs_issues (bug_id, occurrence, ticket_reference, scenario_id)"
             " select %(bug_id)s, %(occurrence)s, %(ticket_reference)s::varchar, %(scenario_tech_id)s"
             " from campaign_ticket_scenarios as cts"
             " join campaign_tickets as ct on ct.id = cts.campaign_ticket_id"
             " join campaigns as ca on ca.id = ct.campaign_id"
             " join scenarios as sc on sc.id = cts.scenario_id"
             " where ca.project_id = %(project_name)s"
             " and ca.version = %(version)s"
             " and ca.occurrence = %(occurrence)s"
             " and ct.ticket_reference = %(ticket_reference)s::varchar"
             " and sc.id = %(scenario_tech_id)s"
             " on conflict do nothing;")
    # Flatten list of related to
    data = [{"bug_id": bug_id,
             "project_name": project_name,
             "version": version,
             "occurrence": elem.occurrence,
             "ticket_reference": str(elem.ticket_reference),
             "scenario_tech_id": elem.scenario_tech_id} for elem in related_to]
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            with connection.cursor() as cursor:
                cursor.executemany(query, data)
                logger.info(f"linked {cursor.rowcount} scenarios to bug {bug_id}")
                if len(data) != cursor.rowcount:
                    raise Exception(f"linked {cursor.rowcount} scenarios to bug {bug_id} while expecting {len(data)}"
                                    f"\n You may have duplicated existing links")
    except Exception as exception:
        logger.error(" ".join(exception.args))
        return 0
    return 1


async def unlink_from_scenario(project_name: str,
                               version: str,
                               unlink_scenario: list[CampaignTicketScenario],
                               bug_id: int,) -> int:
    query = ("delete from bugs_issues"
             " where id in (select id from bugs_issues "
             " where bug_id = %(bug_id)s"
             " and occurrence = %(occurrence)s"
             " and ticket_reference = %(ticket_reference)s::varchar"
             " and scenario_id = %(scenario_tech_id)s);")
    data = [{"bug_id": bug_id,
             "project_name": project_name,
             "version": version,
             "occurrence": elem.occurrence,
             "ticket_reference": str(elem.ticket_reference),
             "scenario_tech_id": elem.scenario_tech_id} for elem in unlink_scenario]
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            with connection.cursor() as cursor:
                cursor.executemany(query, data)
                logger.info(f"unlinked {cursor.rowcount} scenarios from bug {bug_id}")
                if len(data) != cursor.rowcount:
                    raise Exception(
                        f"unlinked {cursor.rowcount} scenarios from bug {bug_id} while expecting {len(data)}"
                        f"\n You may have duplicated existing links")
    except Exception as exception:
        logger.info(repr(exception))
        return 0
    return 1


async def insert_bug(project_name: str,
                     bug_ticket: BugTicket,) -> RegisterVersionResponse:
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
                        f" set {bug_ticket.status.value}_{bug_ticket.criticality}"
                        f" = {bug_ticket.status.value}_{bug_ticket.criticality} + 1"
                        f" from projects as pj"
                        f" where pj.alias = %s"
                        f" and pj.id = ve.project_id"
                        f" and ve.version = %s;")
        connection.execute(update_query, (provide(project_name), bug_ticket.version))
    # TODO Check if a better way is possible
    status_link = await make_link_to_scenario(project_name, bug_ticket.version, bug_ticket.related_to, row[0])
    await rs_invalidate_file(f"file:{project_name}:{bug_ticket.version}:*")
    return RegisterVersionResponse(inserted_id=row[0], message=None if status_link else "Linking fail")
