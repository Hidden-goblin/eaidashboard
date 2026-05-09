# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Tuple

from psycopg import Connection
from psycopg.rows import dict_row, tuple_row

from app.app_exception import StatusTransitionForbidden, UnknownStatusException
from app.database.postgre.pg_utils import _compile
from app.database.postgre.projects.pg_projects import get_projects
from app.database.postgre.versions.versions_query import (
    build_count_project_versions_projection_query,
    build_count_tickets_by_status_query,
    build_current_ticket_query,
    build_get_project_versions_projection_query,
    build_get_project_versions_query,
    build_get_version_query,
    build_get_versions_query,
    build_refresh_versions_query,
    build_update_version_data_query,
    build_update_version_stats_query,
    build_update_version_ticket_status_stats_query,
    build_version_exists_query,
    build_version_internal_id_query,
)
from app.database.utils.transitions import version_transition
from app.schema.bugs_schema import Bugs, UpdateVersion
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.project_enum import ProjectProjections
from app.schema.project_schema import DashboardProject, Statistics
from app.schema.status_enum import StatusEnum, TicketType
from app.schema.versions_schema import Version, VersionProjections
from app.utils.log_management import log_message
from app.utils.pgdb import pool
from app.utils.project_alias import provide


async def version_exists(
    project_name: str,
    version: str,
) -> bool:
    query, params = _compile(build_version_exists_query(provide(project_name), version))
    with pool.connection() as connection:
        row = connection.execute(query, params).fetchone()
        return row is not None


async def get_version(
    project_name: str,
    version: str,
) -> Version:
    """Assuming that project_name and version exists
    :raise TypeError: 'NoneType' object is not subscriptable"""
    query, params = _compile(build_get_version_query(provide(project_name), version))
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(query, params).fetchone()

        stats = Statistics(
            open=row["open"],
            cancelled=row["cancelled"],
            blocked=row["blocked"],
            in_progress=row["in_progress"],
            done=row["done"],
        )
        bugs = Bugs(
            open_blocking=row["open_blocking"],
            open_major=row["open_major"],
            open_minor=row["open_minor"],
            closed_blocking=row["closed_blocking"],
            closed_major=row["closed_major"],
            closed_minor=row["closed_minor"],
        )
        return Version(
            version=version,
            created=row["created"],
            updated=row["updated"],
            started=row["started"],
            end_forecast=row["end_forecast"],
            status=row["status"],
            statistics=stats,
            bugs=bugs,
        )


async def get_versions(
    project_name: str,
    exclude_archived: bool = False,
) -> List[str]:
    query, params = _compile(build_get_versions_query(provide(project_name), exclude_archived))
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return [row[0] for row in connection.execute(query, params).fetchall()]


async def get_project_versions(
    project_name: str,
    exclude_archived: bool = False,
) -> List[Version]:
    query, params = _compile(build_get_project_versions_query(provide(project_name), exclude_archived))
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(query, params).fetchall()
        return _row_to_list_version(rows)


async def get_project_versions_v2(
    project_name: str,
    projection: ProjectProjections,
    limit: int = 10,
    skip: int = 0,
) -> VersionProjections:
    projection_status, exclude_status = _projection_filters(projection)
    query, params = _compile(
        build_get_project_versions_projection_query(
            provide(project_name),
            projection_status,
            exclude_status,
            limit,
            skip,
        )
    )
    count_query, count_params = _compile(
        build_count_project_versions_projection_query(
            provide(project_name),
            projection_status,
            exclude_status,
        )
    )
    with pool.connection() as connection:
        connection.row_factory = dict_row
        conn = connection.execute(query, params).fetchall()
        conn_count = connection.execute(count_query, count_params).fetchone()

        return VersionProjections(count=conn_count["total"], data=_row_to_list_version(conn))


def _row_to_list_version(rows: list) -> List[Version]:
    result = []
    for row in rows:
        stats = Statistics(
            open=row["open"],
            cancelled=row["cancelled"],
            blocked=row["blocked"],
            in_progress=row["in_progress"],
            done=row["done"],
        )
        bugs = Bugs(
            open_blocking=row["open_blocking"],
            open_major=row["open_major"],
            open_minor=row["open_minor"],
            closed_blocking=row["closed_blocking"],
            closed_major=row["closed_major"],
            closed_minor=row["closed_minor"],
        )
        result.append(
            Version(
                version=row["version"],
                created=row["created"],
                updated=row["updated"],
                started=row["started"],
                end_forecast=row["end_forecast"],
                status=row["status"],
                statistics=stats,
                bugs=bugs,
            )
        )
    return result


def _projection_filters(projection: ProjectProjections) -> tuple[str | None, str | None]:
    if projection == ProjectProjections.VERSIONS:
        return None, StatusEnum.ARCHIVED.value
    if projection == ProjectProjections.FUTURE_VERSIONS:
        return StatusEnum.RECORDED.value, None
    if projection == ProjectProjections.ARCHIVED_VERSIONS:
        return StatusEnum.ARCHIVED.value, None
    return None, None


async def update_version_data(
    project_name: str,
    version: str,
    body: UpdateVersion,
) -> Version | ApplicationError:
    updates = {}

    try:
        if body.started is not None:
            updates["started"] = datetime.strptime(
                body.started,
                "%Y-%m-%d",
            )
        if body.end_forecast is not None:
            updates["end_forecast"] = datetime.strptime(
                body.end_forecast,
                "%Y-%m-%d",
            )
    except ValueError as ve:
        return ApplicationError(
            error=ApplicationErrorCode.unknown_status,
            message=" ".join(ve.args),
        )

    if body.status is not None:
        _version = await get_version(
            project_name,
            version,
        )
        try:
            version_transition(
                _version["status"],
                body.status,
            )
        except StatusTransitionForbidden as stf:
            return ApplicationError(
                error=ApplicationErrorCode.transition_forbidden,
                message=" ".join(stf.args),
            )
        except UnknownStatusException as ve:
            return ApplicationError(
                error=ApplicationErrorCode.unknown_status,
                message=" ".join(ve.args),
            )

        updates["status"] = body.status
    if updates:
        updates["updated"] = datetime.now()
        query, params = _compile(build_update_version_data_query(provide(project_name), version, updates))
        with pool.connection() as connection:
            log_message(query)
            connection.execute(query, params)

    return await get_version(
        project_name,
        version,
    )


async def dashboard(
    skip: int = 0,
    limit: int = 10,
) -> Tuple[List[DashboardProject], int]:
    """TODO Fix potential defect where more than 10"""
    projects, count = await get_projects(
        skip,
        limit,
    )
    result = []
    for project in projects:
        project_versions = await get_project_versions(
            project["name"],
            True,
        )
        result.extend(
            {
                "name": project["name"],
                "alias": provide(project["name"]),
                **version.model_dump(),
            }
            for version in project_versions
        )
    return [DashboardProject(**res) for res in result], count


async def update_status_for_ticket_in_version(
    project_name: str,
    version: str,
    ticket_reference: str,
    updated_status: str,
) -> bool | ApplicationError:
    query, params = _compile(build_current_ticket_query(provide(project_name), version, ticket_reference))
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        current_ticket = connection.execute(query, params).fetchone()
        if current_ticket is None:
            return ApplicationError(
                error=ApplicationErrorCode.ticket_not_found,
                message=f"Ticket '{ticket_reference}' does not exist in project '{project_name}' version '{version}'",
            )
        if current_ticket[0] != updated_status:
            update_query, update_params = _compile(
                build_update_version_ticket_status_stats_query(current_ticket[1], current_ticket[0], updated_status)
            )
            row = connection.execute(update_query, update_params)
            log_message(row)
        return True


async def version_internal_id(
    project_name: str,
    version: str,
) -> int | ApplicationError:
    query, params = _compile(build_version_internal_id_query(provide(project_name), version))
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute(query, params).fetchone()
        if result is None:
            return ApplicationError(
                error=ApplicationErrorCode.version_not_found, message=f"The version '{version}' is not found."
            )
        return result[0]


async def refresh_version_stats(
    project_name: str = None,
    version: str = None,
) -> None:
    # TODO: Limit to project-version in general except for future cron task
    query, params = _compile(
        build_refresh_versions_query(
            provide(project_name) if project_name is not None else None,
            version,
        )
    )
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        versions = connection.execute(query, params).fetchall()

        for version_row in versions:
            count_open = _count_tickets_by_status(connection, version_row[0], TicketType.OPEN.value)
            count_in_progress = _count_tickets_by_status(connection, version_row[0], TicketType.IN_PROGRESS.value)
            count_blocked = _count_tickets_by_status(connection, version_row[0], TicketType.BLOCKED.value)
            count_cancelled = _count_tickets_by_status(connection, version_row[0], TicketType.CANCELLED.value)
            count_done = _count_tickets_by_status(connection, version_row[0], TicketType.DONE.value)
            update_query, update_params = _compile(
                build_update_version_stats_query(
                    version_row[0],
                    count_open,
                    count_in_progress,
                    count_blocked,
                    count_cancelled,
                    count_done,
                )
            )
            connection.execute(update_query, update_params)
            connection.commit()


def _count_tickets_by_status(connection: Connection, version_id: int, status: str) -> int:
    query, params = _compile(build_count_tickets_by_status_query(version_id, status))
    return connection.execute(query, params).fetchone()[0]
