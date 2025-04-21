# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from psycopg.rows import dict_row

from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.respository.scenario_schema import BaseScenario, Scenario, Scenarios
from app.utils.pgdb import pool


async def db_get_scenarios(
    project_name: str,
    epic_name: str,
    feature_name: str,
    scenarios_ref: list,
    feature_filename: str = None,
    remove_deleted: bool = True,
) -> Scenarios:
    """

    Args:
        remove_deleted:
        project_name:
        epic_name:
        feature_name:
        scenarios_ref:
        feature_filename:

    Returns: Scenarios

    """
    base_query = """select sc.id as scenario_tech_id,
                sc.scenario_id as scenario_id,
                sc.name as name,
                sc.description as description,
                sc.steps as steps,
                sc.tags as tags,
                sc.isoutline as is_outline,
                sc.is_deleted as is_deleted,
                ft.name as feature_name,
                ft.filename as filename,
                epc.name as epic
                from scenarios as sc
                join features as ft on sc.feature_id = ft.id
                join epics as epc on epc.id = ft.epic_id """
    conditions = [
        "sc.project_id = %s ",
        "epc.name = %s ",
        "ft.name =  %s ",
        "sc.scenario_id =Any(%s)",
    ]
    parameters = [
        project_name.casefold(),
        epic_name,
        feature_name,
        scenarios_ref,
    ]

    if feature_filename is not None:
        conditions.append(" ft.filename = %s")
        parameters.append(feature_filename)

    if remove_deleted:
        conditions.append(" sc.is_deleted = %s")
        parameters.append(False)

    with pool.connection() as connection:
        connection.row_factory = dict_row

        cursor = connection.execute(
            f"{base_query} where {' and '.join(conditions)};",
            parameters,
        )
        return Scenarios(scenarios=[Scenario(**cur) for cur in cursor])


async def db_get_scenarios_id(
    project_name: str,
    epic_name: str,
    feature_name: str,
    scenarios_ref: list | str,
    feature_filename: str = None,
) -> List[int]:
    """
    Test repository scenarios technical id
    Args:
        project_name: Todo check if there is no issue here
        epic_name:
        feature_name:
        scenarios_ref:
        feature_filename:

    Returns:

    """
    if isinstance(scenarios_ref, str):
        scenarios_ref = [scenarios_ref]

    base_query = """select sc.id as id
                from scenarios as sc
                join features as ft on sc.feature_id = ft.id
                join epics as epc on epc.id = ft.epic_id """
    conditions = [
        "sc.project_id = %s ",
        "epc.name = %s ",
        "ft.name =  %s ",
        "sc.scenario_id =Any(%s)",
    ]
    parameters = [
        project_name,
        epic_name,
        feature_name,
        scenarios_ref,
    ]

    if feature_filename is not None:
        conditions.append("ft.filename = %s ")
        parameters.append(feature_filename)

    with pool.connection() as connection:
        connection.row_factory = dict_row

        cursor = connection.execute(
            f"{base_query} where {' and '.join(conditions)};",
            parameters,
        )
        return [row["id"] for row in cursor]


async def db_get_scenario_from_partial(
    project_name: str,
    epic_name: str,
    feature_name: str,
    scenario_ref: str = None,
    scenario_tech_id: int = None,
    feature_filename: str = None,
    active_scenario: bool | None = None,
) -> Scenario | ApplicationError:
    """
    Test repository scenarios technical id
    Args:
        scenario_tech_id:
        active_scenario:
        project_name: Todo check if there is no issue here
        epic_name:
        feature_name:
        scenario_ref:
        feature_filename:

    Returns:

    """
    if scenario_ref is None and scenario_tech_id is None:
        return ApplicationError(
            error=ApplicationErrorCode.value_error, message="A scenario_ref or scenario_tech_id must be provided"
        )
    base_query = """select sc.id as scenario_tech_id,
                sc.scenario_id as scenario_id,
                sc.name as name,
                sc.description as description,
                sc.steps as steps,
                sc.tags as tags,
                sc.isoutline as is_outline,
                sc.is_deleted as is_deleted,
                ft.name as feature_name,
                ft.filename as filename,
                epc.name as epic
                from scenarios as sc
                join features as ft on sc.feature_id = ft.id
                join epics as epc on epc.id = ft.epic_id """
    conditions = [
        "sc.project_id = %s ",
        "epc.name = %s ",
        "ft.name =  %s ",
    ]
    parameters = [
        project_name,
        epic_name,
        feature_name,
    ]
    if scenario_ref is not None:
        conditions.append("sc.scenario_id = %s")
        parameters.append(scenario_ref)

    if scenario_tech_id is not None:
        conditions.append("sc.id = %s")
        parameters.append(scenario_tech_id)

    if feature_filename is not None:
        conditions.append("ft.filename = %s ")
        parameters.append(feature_filename)

    if active_scenario:
        conditions.append("sc.is_deleted = %s")
        parameters.append(False)

    if active_scenario is not None and not active_scenario:
        conditions.append("sc.is_deleted = %s")
        parameters.append(True)

    with pool.connection() as connection:
        connection.row_factory = dict_row

        cursor = connection.execute(
            f"{base_query} where {' and '.join(conditions)};",
            parameters,
        )
        if not cursor.rowcount:
            return ApplicationError(
                error=ApplicationErrorCode.scenario_not_found,
                message=f"'{scenario_ref}' is not found for the project {project_name}'s "
                f"epic-feature '{epic_name}-{feature_name}'",
            )
        return Scenario(**cursor.fetchone())


async def db_update_scenario(
    project_name: str,
    scenario: BaseScenario | ApplicationError,
    is_deleted: bool,
) -> ApplicationError | None:
    """Update a unique scenario in database
    Currently only toggle the is_deleted flag
    """
    if isinstance(scenario, ApplicationError):
        return scenario

    query = """update scenarios as scn
    set is_deleted = %s
    from features as ft
    """
    where_clause = ["scn.feature_id = ft.id", "ft.project_id = %s", "ft.name = %s", "scn.scenario_id = %s"]
    parameters = [is_deleted, project_name, scenario.feature_name, scenario.scenario_id]

    if scenario.filename is not None:
        where_clause.append("ft.filename = %s")
        parameters.append(scenario.filename)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(
            f"{query} where {' and '.join(where_clause)} returning scn.scenario_id",
            parameters,
        ).fetchone()
        connection.commit()

        if cursor is not None:
            return None
        else:
            return ApplicationError(
                error=ApplicationErrorCode.database_no_update,
                message=f"Scenario '{scenario.scenario_id}' has not been {'deleted' if is_deleted else 'activated'}",
            )
