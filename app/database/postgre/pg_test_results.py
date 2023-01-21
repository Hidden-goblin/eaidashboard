# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from psycopg.rows import dict_row, tuple_row

from app.app_exception import DuplicateTestResults
from app.database.mongo.mg_test_results import mg_insert_test_result_done
from app.database.utils.output_strategy import OutputStrategy
from app.database.utils.what_strategy import WhatStrategy
from app.utils.pgdb import pool


def retrieve_tuple_data(result_date, project_name, version, campaign_id, row, is_partial):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        db_row = connection.execute("select ep.id as epic_id, ft.id as feature_id,"
                                    " sc.id as scenario_internal_id from scenarios as sc "
                                    "inner join features as ft on sc.feature_id = ft.id "
                                    "inner join epics as ep on ep.id = ft.epic_id "
                                    "where ep.name = %s "
                                    "and ft.name = %s "
                                    "and sc.scenario_id = %s "
                                    "and ep.project_id = %s;",
                                    (row["epic_id"],
                                     row["feature_name"],
                                     row["scenario_id"],
                                     project_name)).fetchone()
        return (result_date,
                project_name,
                version,
                campaign_id,
                db_row["epic_id"],
                db_row["feature_id"],
                db_row["scenario_internal_id"],
                row["status"],
                is_partial)


def check_result_uniqueness(project_name, version, result_date):
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        if result := connection.execute(
                "select 0 from test_scenario_results "
                "where project_id = %s "
                "and version = %s "
                "and run_date = %s;",
                (project_name, version, result_date),
        ).fetchall():
            raise DuplicateTestResults(f"A test execution result exist for project '{project_name}'"
                                       f" in version '{version}' run at '{result_date}'")


def set_status(current_status, new_result):
    if new_result == "failed" or current_status == "failed":
        return "failed"
    if new_result == "skipped" and current_status == "skipped":
        return "skipped"
    return "passed"



async def insert_result(result_date, project_name, version, campaign_id, is_partial, mg_result_uuid ,rows):
    results = [retrieve_tuple_data(result_date,
                                   project_name,
                                   version,
                                   campaign_id,
                                   row,
                                   is_partial) for row in rows]
    with pool.connection() as connection:
        with connection.cursor().copy("COPY test_scenario_results (run_date, project_id, version,"
                                      " campaign_id, epic_id, feature_id, scenario_id,"
                                      " status, is_partial) from stdin") as copy:
            current_epic = None
            current_epic_status = None
            current_feature = None
            current_feature_status = None
            epics = []
            features = []
            FEATURE_ID_POS: int = 5
            EPIC_ID_POS: int = 4
            RESULT_STATUS_POS: int = 7
            for result in results:
                copy.write_row(result)
                # Feature management
                if current_feature is None:
                    current_feature = result[FEATURE_ID_POS]
                    current_feature_status = result[RESULT_STATUS_POS]
                if current_feature != result[FEATURE_ID_POS]:
                    features.append((result_date,
                                     project_name,
                                     version,
                                     campaign_id,
                                     current_epic,
                                     current_feature,
                                     current_feature_status,
                                     is_partial))
                    current_feature = result[FEATURE_ID_POS]
                    current_feature_status = result[RESULT_STATUS_POS]
                # Epic management
                if current_epic is None:
                    current_epic = result[EPIC_ID_POS]
                    current_epic_status = result[RESULT_STATUS_POS]
                if current_epic != result[EPIC_ID_POS]:
                    epics.append((result_date,
                                     project_name,
                                     version,
                                     campaign_id,
                                     current_epic,
                                     current_epic_status,
                                     is_partial))
                    current_epic = result[EPIC_ID_POS]
                    current_epic_status = result[RESULT_STATUS_POS]
                current_feature_status = set_status(current_feature_status,
                                                    result[RESULT_STATUS_POS])
                current_epic_status = set_status(current_epic_status,
                                                 result[RESULT_STATUS_POS])
            # Last results
            features.append((result_date,
                             project_name,
                             version,
                             campaign_id,
                             current_epic,
                             current_feature,
                             current_feature_status,
                                     is_partial))
            epics.append((result_date,
                          project_name,
                          version,
                          campaign_id,
                          current_epic,
                          current_epic_status,
                                     is_partial))
        with connection.cursor().copy("COPY test_feature_results (run_date, project_id, version,"
                                      " campaign_id, epic_id, feature_id,"
                                      " status, is_partial) from stdin") as copy:
            for feature in features:
                copy.write_row(feature)
        with connection.cursor().copy("COPY test_epic_results (run_date, project_id, version,"
                                      " campaign_id, epic_id,"
                                      " status, is_partial) from stdin") as copy:
            for epic in epics:
                copy.write_row(epic)
    await mg_insert_test_result_done(project_name, mg_result_uuid)
async def retrieve_result(project_name, version: str = None):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        results = connection.execute("select epic_id, feature_id, scenario_id, status, run_date "
                                     "from test_results "
                                     "where project_id = %s "
                                     "order by run_date, epic_id, feature_id;", (project_name,))


        current_epic = ""
        current_epic_status = ""
        current_feature = ""
        current_feature_status = ""
        return_value = {"datetime": [],
                        "epic": {"failed": [], "skipped": [], "passed": []},
                        "feature": {"failed": [], "skipped": [], "passed": []},
                        "scenario": {"failed": [], "skipped": [], "passed": []}}
        current_date = None
        for result in results:

            if not return_value["datetime"]:
                # initial state
                return_value["datetime"].append(result["run_date"])
                current_epic = result["epic_id"]
                current_epic_status = result["status"]
                current_feature = result["feature_id"]
                current_feature_status = result["status"]

            elif result["run_date"] != return_value["datetime"][-1]:
                # new run
                return_value["datetime"].append(result["run_date"])
                current_epic = result["epic_id"]
                current_epic_status = result["status"]
                current_feature = result["feature_id"]
                current_feature_status = result["status"]
            else:
                # current run
                if result["epic_id"] != current_epic:
                    # new epic
                    pass


class TestResults:
    def __init__(self, what: WhatStrategy, output: OutputStrategy):
        self.__what = what
        self.__output = output

    @property
    def what(self):
        return self.__what

    @what.setter
    def what(self, strategy: WhatStrategy):
        self.__what = strategy

    @property
    def output(self):
        return self.__output

    @output.setter
    def output(self, strategy: OutputStrategy):
        self.__output = strategy

    async def render(self, project_name, version, campaign_occurrence):
        table_rows = await self.__what.gather(project_name, version, campaign_occurrence)
        return await self.__output.render(table_rows=table_rows)
