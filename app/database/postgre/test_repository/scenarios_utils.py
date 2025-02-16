# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from psycopg.rows import dict_row

from app.schema.respository.scenario_schema import Scenario, Scenarios
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

    Returns: List of dict

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
        project_name,
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
    scenario_ref: str,
    feature_filename: str = None,
) -> dict:
    """
    Test repository scenarios technical id
    Args:
        project_name: Todo check if there is no issue here
        epic_name:
        feature_name:
        scenario_ref:
        feature_filename:

    Returns:

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
        "sc.scenario_id =%s",
    ]
    parameters = [
        project_name,
        epic_name,
        feature_name,
        scenario_ref,
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
        return cursor.fetchone()
