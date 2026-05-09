# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from sqlalchemy import func, insert, literal, select
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.selectable import Select

from app.database.models.metadata import projects, versions


def build_register_project_query(project_name: str, project_alias: str) -> Insert:
    return insert(projects).values(name=project_name.casefold(), alias=project_alias)


def build_registered_projects_query() -> Select:
    return select(projects.c.name)


def build_get_projects_query(skip: int, limit: int) -> Select:
    future_versions = versions.alias("future_versions")
    archived_versions = versions.alias("archived_versions")
    current_versions = versions.alias("current_versions")

    future_count = (
        select(func.count(future_versions.c.id))
        .where(future_versions.c.project_id == projects.c.id)
        .where(future_versions.c.status == "recorded")
        .scalar_subquery()
    )
    archived_count = (
        select(func.count(archived_versions.c.id))
        .where(archived_versions.c.project_id == projects.c.id)
        .where(archived_versions.c.status == "done")
        .scalar_subquery()
    )
    current_count = (
        select(func.count(current_versions.c.id))
        .where(current_versions.c.project_id == projects.c.id)
        .where(current_versions.c.status != "recorded")
        .where(current_versions.c.status != "done")
        .scalar_subquery()
    )

    return (
        select(
            projects.c.name.label("name"),
            func.coalesce(future_count, 0).label("future"),
            func.coalesce(archived_count, 0).label("archived"),
            func.coalesce(current_count, 0).label("current"),
        )
        .order_by(projects.c.name)
        .limit(limit)
        .offset(skip)
    )


def build_count_projects_query() -> Select:
    return select(func.count(func.distinct(projects.c.id)).label("total"))


def build_create_project_version_query(project_name: str, version: str) -> Insert:
    project_id_query = select(projects.c.id, literal(version)).where(projects.c.alias == project_name)
    return insert(versions).from_select(["project_id", "version"], project_id_query).returning(versions.c.id)


def build_get_project_current_versions_query(project_name: str) -> Select:
    return build_get_project_versions_query(project_name).where(versions.c.status.not_in(["recorded", "archived"]))


def build_get_project_future_versions_query(project_name: str) -> Select:
    return build_get_project_versions_query(project_name).where(versions.c.status == "recorded")


def build_get_project_archived_versions_query(project_name: str) -> Select:
    return build_get_project_versions_query(project_name).where(versions.c.status == "archived")


def build_get_project_versions_query(project_name: str) -> Select:
    return (
        select(
            versions.c.version,
            versions.c.created,
            versions.c.updated,
            versions.c.started,
            versions.c.end_forecast,
            versions.c.status,
        )
        .select_from(versions.join(projects, projects.c.id == versions.c.project_id))
        .where(projects.c.alias == project_name)
    )
