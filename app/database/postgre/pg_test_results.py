# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from csv import DictReader
from datetime import datetime
from typing import List, Tuple

from psycopg.rows import dict_row, tuple_row

from app.app_exception import DuplicateTestResults
from app.database.mongo.mg_test_results import mg_insert_test_result_done
from app.database.utils.output_strategy import OutputStrategy
from app.database.utils.what_strategy import WhatStrategy
from app.utils.pgdb import pool


def retrieve_tuple_data(result_date,
                        project_name,
                        version,
                        campaign_id,
                        row,
                        is_partial) -> Tuple:
    """:return list of tuple (date, str, str, int, int, int, int, str, bool)"""
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


def check_result_uniqueness(project_name: str, version: str, result_date: datetime):
    """Check if result data exist for project_name-version-date exists
    :return None
    :raise DuplicateTestResults"""
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


def set_status(current_status: str, new_result: str) -> str:
    """For container elements, set the status based on the worse status.
    i.e. container element is failed if one of its element is failed
    """
    if new_result == "failed" or current_status == "failed":
        return "failed"
    if new_result == "skipped" and current_status == "skipped":
        return "skipped"
    return "passed"


def __compute_epic_result(epic_list: list,
                          current_epic: int,
                          current_epic_status: str,
                          result_epic: int,
                          result_status: str,
                          result_date,
                          project_name: str,
                          version: str,
                          campaign_id: int,
                          is_partial: bool
                          ) -> Tuple[int, str]:
    if current_epic != result_epic:
        epic_list.append((result_date,
                          project_name,
                          version,
                          campaign_id,
                          current_epic,
                          current_epic_status,
                          is_partial))
    return result_epic, set_status(current_epic_status,result_status)


def __compute_feature_result(feature_list: list,
                             current_feature: int,
                             current_feature_status: str,
                             result_feature: int,
                             result_status: str,
                             result_date,
                             project_name: str,
                             version: str,
                             campaign_id: int,
                             current_epic: int,
                             is_partial: bool) -> Tuple[int, str]:
    if current_feature != result_feature:
        feature_list.append((result_date,
                             project_name,
                             version,
                             campaign_id,
                             current_epic,
                             current_feature,
                             current_feature_status,
                             is_partial))
    return result_feature, set_status(current_feature_status, result_status)


async def insert_result(result_date: datetime,
                        project_name: str,
                        version: str,
                        campaign_id: int,
                        is_partial: bool,
                        mg_result_uuid: str,
                        rows: DictReader | List[dict]):
    results = [retrieve_tuple_data(result_date,
                                   project_name,
                                   version,
                                   campaign_id,
                                   row,
                                   is_partial) for row in rows]
    if not results:
        return await mg_insert_test_result_done(project_name, mg_result_uuid)
    with pool.connection() as connection:
        with connection.cursor().copy("COPY test_scenario_results (run_date, project_id, version,"
                                      " campaign_id, epic_id, feature_id, scenario_id,"
                                      " status, is_partial) from stdin") as copy:

            FEATURE_ID_POS: int = 5
            EPIC_ID_POS: int = 4
            RESULT_STATUS_POS: int = 7

            current_epic = results[0][EPIC_ID_POS]
            current_epic_status = results[0][RESULT_STATUS_POS]
            current_feature = results[0][FEATURE_ID_POS]
            current_feature_status = results[0][RESULT_STATUS_POS]
            epics = []
            features = []
            for result in results:
                copy.write_row(result)

                # Epic management
                current_epic, current_epic_status = __compute_epic_result(
                    epics,
                    current_epic,
                    current_epic_status,
                    result[EPIC_ID_POS],
                    result[RESULT_STATUS_POS],
                    result_date,
                    project_name,
                    version,
                    campaign_id,
                    is_partial
                )

                # Feature management
                current_feature, current_feature_status = __compute_feature_result(
                    features,
                    current_feature,
                    current_feature_status,
                    result[FEATURE_ID_POS],
                    result[RESULT_STATUS_POS],
                    result_date,
                    project_name,
                    version,
                    campaign_id,
                    current_epic,
                    is_partial)

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
