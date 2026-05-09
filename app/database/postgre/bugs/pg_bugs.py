# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from logging import getLogger
from typing import List, Optional

from psycopg.rows import dict_row, tuple_row
from sqlalchemy.dialects import postgresql

from app.database.postgre.bugs.bugs_issues_query import (
    build_delete_bug_issue_query,
    build_get_bugs_issues_query_from_bug_id,
    build_insert_bug_issue_query,
)
from app.database.postgre.bugs.bugs_query import (
    build_get_bug_query,
    build_get_bugs_query,
    build_increment_bug_version_counter_query,
    build_insert_bug_query,
    build_update_bug_query,
    build_update_bug_version_counters_query,
)
from app.database.postgre.versions.pg_versions import version_internal_id
from app.database.redis.rs_file_management import rs_invalidate_file
from app.database.utils.transitions import bug_authorized_transition, version_transition
from app.schema.bugs_schema import BugTicket, BugTicketFull, CampaignTicketScenario, UpdateBugTicket
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.project_schema import RegisterVersionResponse
from app.schema.status_enum import BugStatusEnum
from app.utils.pgdb import pool

logger = getLogger(__name__)


async def get_bugs(
    project_name: str,
    status: Optional[List[BugStatusEnum]] = None,
    criticality: Optional[BugCriticalityEnum] = None,
    version: str = None,
    limit: int = 100,
    skip: int = 0,
) -> tuple[List[BugTicketFull], int]:
    query, count_query = build_get_bugs_query(
        project_name=project_name,
        status=status,
        criticality=criticality,
        version=version,
        limit=limit,
        skip=skip,
    )
    compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})

    compiled_count = count_query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            compiled_query.string,
            compiled_query.params,
        ).fetchall()
        count = connection.execute(
            compiled_count.string,
            compiled_count.params,
        ).fetchone()["total"]

        return [BugTicketFull(**row) for row in rows], count


async def db_get_bug(
    project_name: str,
    internal_id: str,
) -> BugTicketFull | ApplicationError:
    query = build_get_bug_query(project_name=project_name, internal_id=internal_id)

    compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})

    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(compiled_query.string, compiled_query.params).fetchone()
    return (
        BugTicketFull(**row)
        if row
        else ApplicationError(
            error=ApplicationErrorCode.bug_not_found,
            message=f"Bug '{internal_id}' is not found.",
        )
    )


def db_bug_linked_scenario(
    bug_internal_id: Optional[int] = None,
) -> List[CampaignTicketScenario]:
    if bug_internal_id is None:
        return []
    query = build_get_bugs_issues_query_from_bug_id(bug_internal_id)
    compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            compiled_query.string,
            compiled_query.params,
        )
        return [CampaignTicketScenario(**row) for row in rows]


def __update_bug_status(
    current_bug: BugTicketFull,
    bug_ticket: UpdateBugTicket,
    bug_internal_id: int,
) -> None:
    if bug_ticket.status is not None or bug_ticket.criticality is not None:
        open_close_collapse = {
            BugStatusEnum.open: BugStatusEnum.open.value,
            BugStatusEnum.fix_ready: BugStatusEnum.open.value,
            BugStatusEnum.closed: BugStatusEnum.closed.value,
            BugStatusEnum.closed_not_a_defect: BugStatusEnum.closed.value,
        }

        current_status_criticality = f"{open_close_collapse[current_bug.status]}_{current_bug.criticality}"
        to_be_status_criticality = (
            f"{open_close_collapse[bug_ticket.to_dict().get('status', current_bug['status'])]}"
            f"_{bug_ticket.to_dict().get('criticality', current_bug['criticality'])}"
        )
        if current_status_criticality != to_be_status_criticality:
            update_query = build_update_bug_version_counters_query(
                bug_internal_id=bug_internal_id,
                current_status_criticality=current_status_criticality,
                to_be_status_criticality=to_be_status_criticality,
            )
            compiled_query = update_query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True}
            )
            with pool.connection() as connection:
                connection.row_factory = dict_row
                up_version = connection.execute(
                    compiled_query.string,
                    compiled_query.params,
                )
                logger.info(up_version.statusmessage)


async def db_update_bugs(
    project_name: str,
    internal_id: str,
    bug_ticket: UpdateBugTicket,
) -> BugTicketFull | ApplicationError:
    bug_ticket_dict = bug_ticket.to_dict()
    current_bug: BugTicketFull | ApplicationError = await db_get_bug(
        project_name,
        internal_id,
    )
    if isinstance(current_bug, ApplicationError):
        return current_bug

    # Status update must follow transition pattern
    if "status" in bug_ticket_dict.keys():
        version_transition(
            current_bug["status"],
            str(bug_ticket_dict["status"]),
            BugStatusEnum,
            bug_authorized_transition,
        )
    __update_bug_status(
        current_bug,
        bug_ticket,
        int(internal_id),
    )
    update_values = {key: value for key, value in bug_ticket.to_sql().items() if key != "version"}
    version = current_bug.version
    # TIPS: convert string version into internal id version
    if "version" in bug_ticket_dict:
        version = bug_ticket_dict["version"]
        version_id = await version_internal_id(project_name, bug_ticket_dict["version"])
        if isinstance(version_id, ApplicationError):
            return version_id
        update_values["version_id"] = version_id
        # SPEC: Invalidate all files of the future version
        rs_invalidate_file(f"file:{project_name}:{bug_ticket.version}:*")
        # ToDo: update statuses from past version to current version

    update_query = build_update_bug_query(
        internal_id=int(internal_id),
        values=update_values,
    )
    compiled_query = update_query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(
            compiled_query.string,
            compiled_query.params,
        )
        logger.info(row.statusmessage)
    # Link bug to scenario
    if bug_ticket.related_to:
        await make_link_to_scenario(
            project_name,
            version,
            bug_ticket.related_to,
            int(internal_id),
        )
    # Unlink bug to scenario
    if bug_ticket.unlink_scenario:
        await unlink_from_scenario(
            bug_ticket.unlink_scenario,
            int(internal_id),
        )
    # SPEC invalidate all files of the current version
    rs_invalidate_file(f"file:{project_name}:{current_bug.version}:*")
    return await db_get_bug(
        project_name,
        internal_id,
    )


async def make_link_to_scenario(
    project_name: str,
    version: str,
    related_to: List[CampaignTicketScenario],
    bug_id: int,
) -> int:
    data = list(related_to or [])
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            linked_count = 0
            for elem in data:
                query = build_insert_bug_issue_query(
                    project_name=project_name,
                    version=version,
                    bug_id=bug_id,
                    occurrence=elem.occurrence,
                    ticket_reference=str(elem.ticket_reference),
                    scenario_tech_id=elem.scenario_tech_id,
                )
                compiled_query = query.compile(
                    dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True}
                )
                result = connection.execute(
                    compiled_query.string,
                    compiled_query.params,
                )
                linked_count += result.rowcount
            logger.info(f"linked {linked_count} scenarios to bug {bug_id}")
            if len(data) != linked_count:
                raise Exception(
                    f"linked {linked_count} scenarios to bug {bug_id} while expecting {len(data)}"
                    f"\n You may have duplicated existing links"
                )
    except Exception as exception:
        logger.error(" ".join(exception.args))
        return 0
    return 1


async def unlink_from_scenario(
    unlink_scenario: list[CampaignTicketScenario],
    bug_id: int,
) -> int:
    data = list(unlink_scenario or [])
    try:
        with pool.connection() as connection:
            connection.row_factory = dict_row
            unlinked_count = 0
            for elem in data:
                query = build_delete_bug_issue_query(
                    bug_id=bug_id,
                    occurrence=elem.occurrence,
                    ticket_reference=str(elem.ticket_reference),
                    scenario_tech_id=elem.scenario_tech_id,
                )
                compiled_query = query.compile(
                    dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True}
                )
                result = connection.execute(
                    compiled_query.string,
                    compiled_query.params,
                )
                unlinked_count += result.rowcount
            logger.info(f"unlinked {unlinked_count} scenarios from bug {bug_id}")
            if len(data) != unlinked_count:
                raise Exception(
                    f"unlinked {unlinked_count} scenarios from bug {bug_id} while expecting {len(data)}"
                    f"\n You may have duplicated existing links"
                )
    except Exception as exception:
        logger.info(repr(exception))
        return 0
    return 1


async def insert_bug(
    project_name: str,
    bug_ticket: BugTicket,
) -> RegisterVersionResponse:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        query = build_insert_bug_query(
            project_name=project_name,
            title=bug_ticket.title,
            url=bug_ticket.url,
            description=bug_ticket.description,
            version=bug_ticket.version,
            criticality=bug_ticket.criticality.value,
            status=BugStatusEnum.open.value,
        )
        compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})
        row = connection.execute(
            compiled_query.string,
            compiled_query.params,
        ).fetchone()

        update_query = build_increment_bug_version_counter_query(
            project_name=project_name,
            version=bug_ticket.version,
            status_criticality=f"{bug_ticket.status.value}_{bug_ticket.criticality}",
        )
        compiled_update_query = update_query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True}
        )
        connection.execute(compiled_update_query.string, compiled_update_query.params)
    # TODO Check if a better way is possible
    status_link = await make_link_to_scenario(
        project_name,
        bug_ticket.version,
        bug_ticket.related_to,
        row[0],
    )
    rs_invalidate_file(f"file:{project_name}:{bug_ticket.version}:*")
    return RegisterVersionResponse(inserted_id=row[0], message=None if status_link else "Linking fail")
