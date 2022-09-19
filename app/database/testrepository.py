# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.schema.project_schema import TestFeature, TestScenario
from app.utils.pgdb import pool
from psycopg.rows import dict_row


def add_epic(project: str, epic_name: str):
    with pool.connection() as connection:
        connection.execute("insert into epics (name, project_id) "
                           "values (%s, %s)"
                           " on conflict (name, project_id) do nothing;",
                           (epic_name.casefold(), project.casefold()))
        connection.commit()


def add_feature(feature: TestFeature):
    with pool.connection() as connection:
        epic_id = connection.execute(
            "select id from epics"
            " where name = %s "
            "and project_id = %s;",
            (feature["epic_name"].casefold(), feature["project_name"].casefold())).fetchone()[0]
        connection.execute(
            "insert into features (epic_id, name, description, filename, project_id, tags)"
            "values (%(epic)s, %(name)s, %(description)s, %(filename)s, %(project)s, %(tags)s)"
            "on conflict (project_id, filename) do "
            "update set name = %(name)s,"
            " description = %(description)s,"
            " tags = %(tags)s"
            " where features.filename = %(filename)s "
            "and features.project_id = %(project)s ;",
            {"epic": epic_id, "name": feature["feature_name"],
             "description": feature["description"], "filename": feature["filename"],
             "project": feature["project_name"], "tags": feature["tags"]})
        connection.commit()


def add_scenario(scenario: TestScenario):
    with pool.connection() as connection:
        feature_id = connection.execute(
            "select id from features where filename = %s and project_id = %s;",
            (scenario["filename"], scenario["project_name"])).fetchone()[0]
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
            {"sc_id": scenario["scenario_id"], "ftr_id": feature_id, "sc_name": scenario["name"],
             "sc_desc": scenario["description"], "sc_steps": scenario["steps"],
             "sc_tags": scenario["tags"], "sc_outline": scenario["is_outline"],
             "project": scenario["project_name"]}
        )
        connection.commit()


def clean_scenario_with_fake_id(project: str):
    with pool.connection() as connection:
        connection.execute(
            "delete from scenarios "
            "where "
            " project_id = %s and scenario_id like  %s;",
            (project, "XXX-application-undefined-id-%")
                           )
        connection.commit()


def db_project_epics(project: str, limit: int = 100, offset: int = 0):
    with pool.connection() as connection:
        cursor = connection.execute(
            "select name from epics "
            "where project_id = %s "
            "order by name "
            "limit %s offset %s", (project.casefold(), limit, offset)
        )
        return [row[0] for row in cursor]


def db_project_features(project: str, epic: str = None, limit: int = 100, offset: int = 0):
    with pool.connection() as connection:
        cursor = None
        if epic is not None:
            cursor = connection.execute(
                "select features.name, tags, filename from features "
                "join epics on epics.id = features.epic_id "
                "where features.project_id = %s and epics.name = %s "
                "order by features.name "
                "limit %s offset %s", (project.casefold(), epic, limit, offset)
            )
        else:
            cursor = connection.execute(
                "select name, tags, filename from features "
                "where project_id = %s "
                "order by name "
                "limit %s  offset %s", (project.casefold(), limit, offset)
            )
        return [{"name": row[0],
                 "tags": row[1],
                 "filename": row[2]} for row in cursor]


def db_project_scenarios(project: str, epic: str = None, feature: str = None,
                         limit: int = 100, offset: int = 0):
    with pool.connection() as connection:
        cursor = None
        if epic is not None and feature is not None:
            cursor = connection.execute(
                "select epics.name, features.name, features.filename, scenarios.id,"
                " scenarios.scenario_id,"
                " scenarios.name, scenarios.tags, scenarios.steps from scenarios "
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
        elif epic is not None:
            cursor = connection.execute(
                "select epics.name, features.name, features.filename, scenarios.id, "
                "scenarios.scenario_id, "
                "scenarios.name, scenarios.tags, scenarios.steps from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and epics.name like %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s"
                , (project.casefold(), f"%{epic}%", limit, offset)
            )
        elif feature is not None:
            cursor = connection.execute(
                "select epics.name, features.name, features.filename, scenarios.id, "
                "scenarios.scenario_id, "
                "scenarios.name, scenarios.tags, scenarios.steps from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "and features.name like %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s"
                , (project.casefold(),  f"%{feature}%", limit, offset)
            )
        else:
            cursor = connection.execute(
                "select epics.name, features.name, features.filename, scenarios.id, "
                "scenarios.scenario_id, "
                "scenarios.name, scenarios.tags, scenarios.steps from scenarios "
                "full join features on features.id = scenarios.feature_id "
                "full join epics on epics.id = features.epic_id "
                "where scenarios.project_id = %s "
                "order by epics.name,"
                " features.filename,"
                " scenarios.scenario_id "
                "limit %s offset %s"
                , (project.casefold(), limit, offset)
            )
        return [{"epic": row[0],
                 "feature_name": row[1],
                 "filename": row[2],
                 "scenario_tech_id": row[3],
                 "scenario_id": row[4],
                 "name": row[5],
                 "tags": row[6],
                 "steps": row[7]} for row in cursor]
