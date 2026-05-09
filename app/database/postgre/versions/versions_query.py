# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from sqlalchemy import Select, Update, func, select, update

from app.database.models.metadata import projects, tickets, versions
from app.schema.status_enum import StatusEnum


def build_version_exists_query(project_name: str, version: str) -> Select:
    return (
        select(versions.c.id)
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
        .where(versions.c.version == version)
    )


def build_get_version_query(project_name: str, version: str) -> Select:
    return (
        select(versions)
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
        .where(versions.c.version == version)
    )


def build_get_versions_query(project_name: str, exclude_archived: bool = False) -> Select:
    query = (
        select(versions.c.version)
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
    )
    if exclude_archived:
        query = query.where(versions.c.status != StatusEnum.ARCHIVED.value)
    return query


def build_get_project_versions_query(project_name: str, exclude_archived: bool = False) -> Select:
    query = (
        select(versions)
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
    )
    if exclude_archived:
        query = query.where(versions.c.status != StatusEnum.ARCHIVED.value)
    return query


def build_get_project_versions_projection_query(
    project_name: str,
    projection_status: str | None,
    exclude_status: str | None,
    limit: int,
    skip: int,
) -> Select:
    return (
        _project_versions_projection_base_query(project_name, projection_status, exclude_status)
        .order_by(versions.c.created.desc())
        .limit(limit)
        .offset(skip)
    )


def build_count_project_versions_projection_query(
    project_name: str,
    projection_status: str | None,
    exclude_status: str | None,
) -> Select:
    return _project_versions_projection_base_query(project_name, projection_status, exclude_status).with_only_columns(
        func.count(versions.c.id).label("total")
    )


def build_update_version_data_query(project_name: str, version: str, updates: dict[str, Any]) -> Update:
    return (
        update(versions)
        .values(**updates)
        .where(projects.c.alias == project_name)
        .where(projects.c.id == versions.c.project_id)
        .where(versions.c.version == version)
    )


def build_current_ticket_query(project_name: str, version: str, ticket_reference: str) -> Select:
    return (
        select(tickets.c.status, tickets.c.current_version)
        .select_from(
            tickets.join(versions, tickets.c.current_version == versions.c.id).join(
                projects,
                projects.c.id == versions.c.project_id,
            )
        )
        .where(projects.c.alias == project_name)
        .where(versions.c.version == version)
        .where(tickets.c.reference == ticket_reference)
    )


def build_update_version_ticket_status_stats_query(version_id: int, current_status: str, updated_status: str) -> Update:
    return (
        update(versions)
        .values(
            {
                current_status: versions.c[current_status] - 1,
                updated_status: versions.c[updated_status] + 1,
            }
        )
        .where(versions.c.id == version_id)
    )


def build_version_internal_id_query(project_name: str, version: str) -> Select:
    return (
        select(versions.c.id)
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
        .where(versions.c.version == version)
    )


def build_refresh_versions_query(project_name: str | None = None, version: str | None = None) -> Select:
    query = select(versions.c.id)
    if project_name is not None:
        query = query.select_from(versions.join(projects, projects.c.id == versions.c.project_id)).where(
            projects.c.alias == project_name
        )
    if version is not None:
        query = query.where(versions.c.version == version)
    return query


def build_count_tickets_by_status_query(version_id: int, status: str) -> Select:
    return (
        select(func.count(tickets.c.id))
        .where(tickets.c.current_version == version_id)
        .where(tickets.c.status == status)
    )


def build_update_version_stats_query(
    version_id: int,
    count_open: int,
    count_in_progress: int,
    count_blocked: int,
    count_cancelled: int,
    count_done: int,
) -> Update:
    return (
        update(versions)
        .values(
            open=count_open,
            in_progress=count_in_progress,
            blocked=count_blocked,
            cancelled=count_cancelled,
            done=count_done,
        )
        .where(versions.c.id == version_id)
    )


def _project_versions_projection_base_query(
    project_name: str,
    projection_status: str | None,
    exclude_status: str | None,
) -> Select:
    query = (
        select(versions)
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
    )
    if projection_status is not None:
        query = query.where(versions.c.status == projection_status)
    if exclude_status is not None:
        query = query.where(versions.c.status != exclude_status)
    return query
