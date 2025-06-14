# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import asyncio
from typing import List, Tuple

from psycopg.rows import dict_row, tuple_row

from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.repository_schema import TestFeature, TestScenario
from app.schema.respository.epic_schema import Epic
from app.schema.respository.feature_schema import Feature
from app.schema.respository.scenario_schema import Scenario, Scenarios
from app.utils.pgdb import pool


async def add_epic(
    project: str,
    epic_name: str,
) -> None:
    with pool.connection() as connection:
        connection.execute(
            "insert into epics (name, project_id) values (%s, %s) on conflict (name, project_id) do nothing;",
            (
                epic_name.casefold(),
                project.casefold(),
            ),
        )
        connection.commit()


async def add_feature(feature: TestFeature) -> None:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        epic_id = connection.execute(
            "select id from epics where name = %s and project_id = %s;",
            (
                feature.epic_name.casefold(),
                feature.project_name.casefold(),
            ),
        ).fetchone()[0]
        # Ensure Epic id is retrieved
        connection.execute(
            "insert into features (epic_id, name, description, filename, project_id, tags)"
            "values (%(epic)s, %(name)s, %(description)s, %(filename)s, %(project)s, %(tags)s)"
            "on conflict (project_id, filename) do "
            "update set name = %(name)s,"
            " description = %(description)s,"
            " tags = %(tags)s"
            " where features.filename = %(filename)s "
            "and features.project_id = %(project)s ;",
            {
                "epic": epic_id,
                "name": feature.feature_name,
                "description": feature.description,
                "filename": feature.filename,
                "project": feature.project_name,
                "tags": feature.tags,
            },
        )
        connection.commit()


async def add_scenario(
    scenario: TestScenario,
) -> None:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        feature_id = connection.execute(
            "select id from features where filename = %s and project_id = %s;",
            (
                scenario.filename,
                scenario.project_name,
            ),
        ).fetchone()[0]
        # Ensure feature_id is retrieved
        connection.execute(
            "insert into scenarios "
            "(scenario_id, feature_id, name, description, steps, tags, isoutline, project_id)"
            "values (%(sc_id)s, %(ftr_id)s, %(sc_name)s, %(sc_desc)s, %(sc_steps)s,%(sc_tags)s,"
            " %(sc_outline)s, %(project)s) on conflict (scenario_id, feature_id, project_id)"
            " do update set name = %(sc_name)s,"
            "description = %(sc_desc)s,"
            "steps = %(sc_steps)s,"
            "tags = %(sc_tags)s,"
            "isoutline = %(sc_outline)s,"
            "is_deleted = FALSE "
            "where scenarios.scenario_id = %(sc_id)s "
            "and scenarios.feature_id = %(ftr_id)s "
            "and scenarios.project_id = %(project)s;",
            {
                "sc_id": scenario.scenario_id,
                "ftr_id": feature_id,
                "sc_name": scenario.name,
                "sc_desc": scenario.description,
                "sc_steps": scenario.steps,
                "sc_tags": scenario.tags,
                "sc_outline": scenario.is_outline,
                "project": scenario.project_name,
            },
        )
        connection.commit()


async def clean_scenario_with_fake_id(
    project: str,
) -> None:
    with pool.connection() as connection:
        connection.execute(
            "delete from scenarios where project_id = %s and scenario_id like  %s;",
            (
                project,
                "XXX-application-undefined-id-%",
            ),
        )
        connection.commit()


async def db_project_epics(
    project: str,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[str], int]:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(
            "select name as name from epics where project_id = %s order by name limit %s offset %s",
            (
                project.casefold(),
                limit,
                offset,
            ),
        )
        count = connection.execute(
            "select count(*) as total from epics where project_id = %s",
            (project.casefold(),),
        )
        return [row["name"] for row in cursor], count.fetchone()["total"]


async def db_project_epic(
    project_name: str,
    epic_ref: str,
) -> Epic | ApplicationError:
    """

    Args:
        project_name:
        epic_ref:

    Returns: The Epic object or an ApplicationError when not found

    """
    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(
            "select name as epic_name,"
            " project_id as project_name,"
            " id as epic_tech_id "
            "from epics where project_id = %s and name = %s;",
            (project_name.casefold(), epic_ref),
        ).fetchone()
        if cursor is not None:
            return Epic(**cursor)
        else:
            return ApplicationError(
                error=ApplicationErrorCode.epic_not_found,
                message=f"Epic '{epic_ref}' not found in project '{project_name}'.",
            )


async def db_project_features(
    project: str,
    epic: str = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Feature] | ApplicationError, int]:
    """Return all features either bound to a project or a project's feature"""
    if epic is not None:
        return await __epic_all_features(project, epic, limit, offset)
    else:
        return await __project_all_features(project, limit, offset)


async def __project_all_features(project: str, limit: int, offset: int) -> (List[Feature], int):
    """Retrieve all paginated features of a project"""
    count_query = "select count(*) as total  from features where project_id =%s"
    select_query = (
        "select features.name as name,"
        " tags as tags,"
        " filename as filename"
        " from features"
        " where project_id = %s"
        " order by name "
        " limit %s  offset %s"
    )
    with pool.connection() as connection:
        connection.row_factory = dict_row
        count = connection.execute(count_query, (project,))
        select = connection.execute(
            select_query,
            (
                project,
                limit,
                offset,
            ),
        )

    return [Feature(**cur) for cur in select], count.fetchone()["total"]


async def __epic_all_features(
    project: str,
    epic: str = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Feature] | ApplicationError, int]:
    if isinstance(_epic := await db_project_epic(project, epic), ApplicationError):
        return _epic, -1

    select_query = (
        "select features.name as name,"
        " tags as tags,"
        " filename as filename"
        " from features "
        "join epics on epics.id = features.epic_id "
        "where features.project_id = %s and epics.name = %s "
        "order by features.name "
        "limit %s offset %s"
    )

    count_query = (
        "select count(*) as total"
        " from features "
        "join epics on epics.id = features.epic_id "
        "where features.project_id = %s and epics.name = %s "
    )
    with pool.connection() as connection:
        connection.row_factory = dict_row
        count = connection.execute(count_query, (project, epic))
        select = connection.execute(
            select_query,
            (
                project,
                epic,
                limit,
                offset,
            ),
        )

    return [Feature(**cur) for cur in select], count.fetchone()["total"]


async def db_project_feature(
    project_name: str,
    epic_ref: str,
    feature_name: str,
) -> Feature | ApplicationError:
    """
    Retrieve Feature from a project using the feature name and epic name
    Args:
        project_name:
        epic_ref: epic name as reference
        feature_name:

    Returns: Feature or ApplicationError where the query returns nothing
    """
    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(
            "select ft.name,"
            " ft.tags,"
            " ft.filename"
            " from features as ft"
            " join epics as ep on ep.id = ft.epic_id"
            " where ft.project_id = %s and ft.name = %s and ep.name = %s;",
            (
                project_name.casefold(),
                feature_name,
                epic_ref,
            ),
        ).fetchone()
        if cursor is not None:
            return Feature(**cursor)
        else:
            return ApplicationError(
                error=ApplicationErrorCode.feature_not_found,
                message=f"Feature '{feature_name}' not found in project '{project_name}' and epic '{epic_ref}.",
            )


async def db_project_scenarios(
    project: str,
    epic: str = None,
    feature: str = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Scenario], int]:
    """All scenarios for a project"""
    base_query = """
        select epics.name as epic,
               features.name as feature_name,
               features.filename as filename,
               scenarios.id as scenario_tech_id,
               scenarios.scenario_id as scenario_id,
               scenarios.name as name,
               scenarios.tags as tags,
               scenarios.steps as steps
          from scenarios
     full join features on features.id = scenarios.feature_id
     full join epics on epics.id = features.epic_id
    """

    count_query = """
        select count(*) as total
          from scenarios
     full join features on features.id = scenarios.feature_id
     full join epics on epics.id = features.epic_id
    """

    conditions = [
        "scenarios.project_id = %s",
        "scenarios.is_deleted = False",
    ]
    params = [project.casefold()]

    if epic:
        conditions.append("epics.name = %s")
        params.append(epic)
    if feature:
        conditions.append("features.name = %s")
        params.append(feature)

    # Add conditions to the queries
    base_query = f"""{base_query}
                    where {" and ".join(conditions)}
                    order by epics.name,
                        features.filename,
                        scenarios.scenario_id
                    limit %s offset %s; """
    count_query = f"{count_query} where {' and '.join(conditions)};"
    params.extend([limit, offset])

    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(base_query, tuple(params))
        count = connection.execute(count_query, tuple(params[:-2]))

    return [Scenario(**cur) for cur in cursor], count.fetchone()["total"]


async def db_scenarios(
    project_name: str,
    epic_ref: str,
    feature_ref: str,
    limit: int = 100,
    offset: int = 0,
) -> Scenarios:
    """
    Retrieve scenarios from db
    Check epic_ref and feature_ref existence
    Args:
        project_name:
        epic_ref:
        feature_ref:
        limit:
        offset:

    Returns:

    """
    async with asyncio.TaskGroup() as tg:
        _epic = tg.create_task(
            db_project_epic(
                project_name,
                epic_ref,
            ),
        )

        _feature = tg.create_task(
            db_project_feature(
                project_name,
                epic_ref,
                feature_ref,
            ),
        )

    if isinstance(_epic.result(), ApplicationError):
        return _epic.result()
    if isinstance(_feature.result(), ApplicationError):
        return _feature.result()

    query = """select sc.id as scenario_tech_id,
    sc.scenario_id as scenario_id,
    sc.name as name,
    sc.tags as tags,
    sc.steps as steps,
    sc.isoutline as is_outline,
    sc.is_deleted as is_deleted,
    ft.name as feature_name,
    ft.filename as filename,
    epc.name as epic
     from scenarios as sc
    join features as ft on ft.id = sc.feature_id
    join epics as epc on epc.id = ft.epic_id
    where epc.project_id = %s
    and epc.name = %s
    and ft.name = %s
    order by ft.filename,
             sc.scenario_id
    limit %s offset %s;
    """
    parameters = [
        project_name.casefold(),
        epic_ref,
        feature_ref,
        limit,
        offset,
    ]

    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(query, parameters)

        return Scenarios(scenarios=[Scenario(**row) for row in cursor])
