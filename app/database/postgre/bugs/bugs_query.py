from logging import getLogger
from typing import Any, List, Optional

from sqlalchemy import String, and_, cast, func, insert, literal, select, text, update
from sqlalchemy.sql.dml import Insert, Update
from sqlalchemy.sql.selectable import Select

from app.database.models.metadata import bugs, bugs_issues, projects, versions
from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.status_enum import BugStatusEnum
from app.utils.project_alias import provide

logger = getLogger(__name__)


def build_get_bugs_query(
    project_name: str,
    status: Optional[List[BugStatusEnum]] = None,
    criticality: Optional[BugCriticalityEnum] = None,
    version: str = None,
    limit: int = 100,
    skip: int = 0,
) -> tuple[Select, Select]:
    logger.info(
        f"called with project_name: {project_name}, status: {status}, criticality: {criticality},"
        f" version: {version}, limit: {limit}, skip: {skip}"
    )
    related_to = func.json_agg(
        func.json_strip_nulls(
            func.json_build_object(
                text("'occurrence'"),
                bugs_issues.c.occurrence,
                text("'ticket_reference'"),
                bugs_issues.c.ticket_reference,
                text("'scenario_tech_id'"),
                bugs_issues.c.scenario_id,
            )
        )
    ).label("related_to")

    query = select(
        bugs.c.id.label("internal_id"),
        bugs.c.title,
        bugs.c.url,
        bugs.c.description,
        versions.c.version,
        bugs.c.criticality,
        bugs.c.status,
        bugs.c.created,
        bugs.c.updated,
        related_to,
    ).select_from(
        bugs.join(projects, projects.c.id == bugs.c.project_id)
        .join(versions, versions.c.id == bugs.c.version_id)
        .outerjoin(bugs_issues, bugs_issues.c.bug_id == bugs.c.id)
    )

    filters = [projects.c.alias == cast(provide(project_name), String)]

    if version:
        filters.append(versions.c.version == version)

    if status:
        filters.append(bugs.c.status.in_([cast(str(s), String) for s in status]))

    if criticality:
        filters.append(bugs.c.criticality == cast(criticality.value, String))

    query = (
        query.where(and_(*filters))
        .group_by(bugs.c.id, versions.c.version)
        .order_by(versions.c.version, bugs.c.id)
        .limit(limit)
        .offset(skip)
    )

    # Count query
    count_query = (
        select(func.count(bugs.c.id).label("total"))
        .select_from(
            bugs.join(projects, projects.c.id == bugs.c.project_id).join(versions, versions.c.id == bugs.c.version_id)
        )
        .where(and_(*filters))
    )

    return query, count_query


def build_get_bug_query(
    project_name: str,
    internal_id: str,
) -> Select:
    logger.info(f"called with project_name: {project_name}, internal_id: {internal_id}")
    related_to = func.json_agg(
        func.json_strip_nulls(
            func.json_build_object(
                text("'occurrence'"),
                bugs_issues.c.occurrence,
                text("'ticket_reference'"),
                bugs_issues.c.ticket_reference,
                text("'scenario_tech_id'"),
                bugs_issues.c.scenario_id,
            )
        )
    ).label("related_to")

    filters = [
        projects.c.alias == cast(provide(project_name), String),
        bugs.c.id == internal_id,
    ]
    query = (
        select(
            bugs.c.id.label("internal_id"),
            bugs.c.title,
            bugs.c.url,
            bugs.c.description,
            versions.c.version,
            bugs.c.criticality,
            bugs.c.status,
            bugs.c.created,
            bugs.c.updated,
            related_to,
        )
        .select_from(
            bugs.join(projects, projects.c.id == bugs.c.project_id)
            .join(versions, versions.c.id == bugs.c.version_id)
            .outerjoin(bugs_issues, bugs_issues.c.bug_id == bugs.c.id)
        )
        .where(and_(*filters))
        .group_by(bugs.c.id, versions.c.version)
    )

    return query


def build_update_bug_query(
    internal_id: int,
    values: dict[str, Any],
) -> Update:
    logger.info(f"called with internal_id: {internal_id}, fields: {list(values.keys())}")
    return update(bugs).where(bugs.c.id == internal_id).values(**values).returning(bugs.c.id)


def build_insert_bug_query(
    project_name: str,
    title: str,
    url: str | None,
    description: str,
    version: str,
    criticality: str,
    status: str,
) -> Insert:
    logger.info("called with project_name: %s, version: %s, title: %s", project_name, version, title)
    select_query = (
        select(
            literal(title),
            literal(url),
            literal(description),
            projects.c.id,
            versions.c.id,
            literal(criticality),
            literal(status),
        )
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(versions.c.version == version)
        .where(projects.c.alias == provide(project_name))
    )

    return (
        insert(bugs)
        .from_select(
            ["title", "url", "description", "project_id", "version_id", "criticality", "status"],
            select_query,
        )
        .returning(bugs.c.id)
    )


def build_increment_bug_version_counter_query(
    project_name: str,
    version: str,
    status_criticality: str,
) -> Update:
    logger.info(
        "called with project_name: %s, version: %s, status_criticality: %s",
        project_name,
        version,
        status_criticality,
    )
    project_id_subquery = select(projects.c.id).where(projects.c.alias == provide(project_name)).scalar_subquery()
    return (
        update(versions)
        .where(versions.c.project_id == project_id_subquery)
        .where(versions.c.version == version)
        .values({status_criticality: versions.c[status_criticality] + 1})
    )


def build_update_bug_version_counters_query(
    bug_internal_id: int,
    current_status_criticality: str,
    to_be_status_criticality: str,
) -> Update:
    logger.info(
        f"called with bug_internal_id: {bug_internal_id}, current_status_criticality: {current_status_criticality},"
        f" to_be_status_criticality: {to_be_status_criticality}"
    )
    version_id_subquery = select(bugs.c.version_id).where(bugs.c.id == bug_internal_id).scalar_subquery()
    return (
        update(versions)
        .where(versions.c.id == version_id_subquery)
        .values(
            {
                current_status_criticality: versions.c[current_status_criticality] - 1,
                to_be_status_criticality: versions.c[to_be_status_criticality] + 1,
            }
        )
    )
