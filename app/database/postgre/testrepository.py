# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Tuple

from psycopg.rows import dict_row, tuple_row

from app.schema.repository_schema import Feature, Scenario, TestFeature, TestScenario
from app.utils.pgdb import pool


async def add_epic(project: str, epic_name: str) -> None:
    with pool.connection() as connection:
        connection.execute("insert into epics (name, project_id) "
                           "values (%s, %s)"
                           " on conflict (name, project_id) do nothing;",
                           (epic_name.casefold(), project.casefold()))
        connection.commit()


async def add_feature(feature: TestFeature) -> None:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        epic_id = connection.execute(
            "select id from epics"
            " where name = %s "
            "and project_id = %s;",
            (feature.epic_name.casefold(),
             feature.project_name.casefold())).fetchone()[0]
        connection.execute(
            "insert into features (epic_id, name, description, filename, project_id, tags)"
            "values (%(epic)s, %(name)s, %(description)s, %(filename)s, %(project)s, %(tags)s)"
            "on conflict (project_id, filename) do "
            "update set name = %(name)s,"
            " description = %(description)s,"
            " tags = %(tags)s"
            " where features.filename = %(filename)s "
            "and features.project_id = %(project)s ;",
            {"epic": epic_id,
             "name": feature.feature_name,
             "description": feature.description,
             "filename": feature.filename,
             "project": feature.project_name,
             "tags": feature.tags})
        connection.commit()


async def add_scenario(scenario: TestScenario) -> None:
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        feature_id = connection.execute(
            "select id from features where filename = %s and project_id = %s;",
            (scenario.filename, scenario.project_name)).fetchone()[0]
        connection.execute(
            "insert into scenarios "
            "(scenario_id, feature_id, name, description, steps, tags, isoutline, project_id)"
            "values (%(sc_id)s, %(ftr_id)s, %(sc_name)s, %(sc_desc)s, %(sc_steps)s,%(sc_tags)s,"
            " %(sc_outline)s, %(project)s) on conflict (scenario_id, feature_id, project_id)"
            " do update set name = %(sc_name)s,"
            "description = %(sc_desc)s,"
            "steps = %(sc_steps)s,"
            "tags = %(sc_tags)s,"
            "isoutline = %(sc_outline)s "
            "where scenarios.scenario_id = %(sc_id)s "
            "and scenarios.feature_id = %(ftr_id)s "
            "and scenarios.project_id = %(project)s;",
            {"sc_id": scenario.scenario_id,
             "ftr_id": feature_id,
             "sc_name": scenario.name,
             "sc_desc": scenario.description,
             "sc_steps": scenario.steps,
             "sc_tags": scenario.tags,
             "sc_outline": scenario.is_outline,
             "project": scenario.project_name}
        )
        connection.commit()


async def clean_scenario_with_fake_id(project: str) -> None:
    with pool.connection() as connection:
        connection.execute(
            "delete from scenarios "
            "where "
            " project_id = %s and scenario_id like  %s;",
            (project, "XXX-application-undefined-id-%")
        )
        connection.commit()


async def db_project_epics(project: str,
                           limit: int = 100,
                           offset: int = 0) -> List[str]:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = connection.execute(
            "select name as name from epics "
            "where project_id = %s "
            "order by name "
            "limit %s offset %s", (project.casefold(), limit, offset)
        )
        return [row["name"] for row in cursor]


async def db_project_features(project: str,
                              epic: str = None,
                              limit: int = 100,
                              offset: int = 0) -> List[Feature]:
    with pool.connection() as connection:
        cursor = None
        connection.row_factory = dict_row
        if epic is not None:
            cursor = connection.execute(
                "select features.name as name, tags as tags, filename as filename from features "
                "join epics on epics.id = features.epic_id "
                "where features.project_id = %s and epics.name = %s "
                "order by features.name "
                "limit %s offset %s", (project.casefold(), epic, limit, offset)
            )
        else:
            cursor = connection.execute(
                "select features.name as name, tags as tags, filename as filename from features "
                "where project_id = %s "
                "order by name "
                "limit %s  offset %s", (project.casefold(), limit, offset)
            )
        return [Feature(**cur) for cur in cursor]


async def db_project_scenarios(project: str,
                               epic: str = None,
                               feature: str = None,
                               limit: int = 100,
                               offset: int = 0) -> Tuple[List[Scenario], int]:
    """All scenarios for a project"""
    with pool.connection() as connection:
        connection.row_factory = dict_row
        cursor = None
        count = None
        if epic is not None and feature is not None:
            cursor = connection.execute(
                "select epics.name as epic, features.name as feature_name, "
                "features.filename as filename, scenarios.id as scenario_tech_id,"
                " scenarios.scenario_id as scenario_id,"
                " scenarios.name as name, scenarios.tags as tags, "
                "scenarios.steps as steps from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and epics.name like %s "
                "and features.name like %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s", (project.casefold(), f"%{epic}%",
                                       f"%{feature}%", limit, offset)
            )
            count = connection.execute(
                "select count(*) as total from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and epics.name like %s "
                "and features.name like %s ",
                (project.casefold(), f"%{epic}%", f"%{feature}%"))
        elif epic is not None:
            cursor = connection.execute(
                "select epics.name as epic, features.name as feature_name, "
                "features.filename as filename, scenarios.id as scenario_tech_id,"
                " scenarios.scenario_id as scenario_id,"
                " scenarios.name as name, scenarios.tags as tags, "
                "scenarios.steps as steps from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and epics.name like %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s",
                (project.casefold(), f"%{epic}%", limit, offset)
            )
            count = connection.execute(
                "select count(*) as total from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and epics.name like %s ",
                (project.casefold(), f"%{epic}%"))
        elif feature is not None:
            cursor = connection.execute(
                "select epics.name as epic, features.name as feature_name, "
                "features.filename as filename, scenarios.id as scenario_tech_id,"
                " scenarios.scenario_id as scenario_id,"
                " scenarios.name as name, scenarios.tags as tags, "
                "scenarios.steps as steps from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and features.name like %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s",
                (project.casefold(), f"%{feature}%", limit, offset)
            )
            count = connection.execute(
                "select count(*) as total from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and features.name like %s ",
                (project.casefold(), f"%{feature}%"))
        else:
            cursor = connection.execute(
                "select epics.name as epic, features.name as feature_name, "
                "features.filename as filename, scenarios.id as scenario_tech_id,"
                " scenarios.scenario_id as scenario_id,"
                " scenarios.name as name, scenarios.tags as tags, "
                "scenarios.steps as steps"
                " from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s",
                (project.casefold(), limit, offset)
            )
            count = connection.execute(
                "select count(*) as total from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s ",
                (project.casefold(),))
        return [Scenario(**cur) for cur in cursor], count.fetchone()["total"]


async def db_get_scenarios_id(project_name: str,
                              epic_name: str,
                              feature_name: str,
                              scenarios_ref: list | str,
                              feature_filename: str=None) -> List[int]:
    if isinstance(scenarios_ref, str):
        scenarios_ref = [scenarios_ref]
    with pool.connection() as connection:
        connection.row_factory = dict_row
        if feature_filename is None:
            cursor = connection.execute("select sc.id "
                                        "from scenarios as sc "
                                        "join features as ft on sc.feature_id = ft.id "
                                        "join epics as epc on epc.id = ft.epic_id "
                                        "where sc.project_id like %s "
                                        "and epc.name like %s "
                                        "and ft.name like  %s "
                                        "and sc.scenario_id =Any(%s);", [project_name,
                                                                         epic_name,
                                                                         feature_name,
                                                                         scenarios_ref])
        else:
            cursor = connection.execute("select sc.id "
                                        "from scenarios as sc "
                                        "join features as ft on sc.feature_id = ft.id "
                                        "join epics as epc on epc.id = ft.epic_id "
                                        "where sc.project_id like %s "
                                        "and epc.name like %s "
                                        "and ft.name like  %s "
                                        "and ft.filename like %s "
                                        "and sc.scenario_id =Any(%s);", [project_name,
                                                                         epic_name,
                                                                         feature_name,
                                                                         feature_filename,
                                                                         scenarios_ref])
        return [row["id"] for row in cursor]
