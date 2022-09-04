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
