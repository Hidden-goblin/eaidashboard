# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from csv import DictReader
from datetime import datetime
from typing import List, Tuple

from psycopg.rows import dict_row, tuple_row

from app.app_exception import DuplicateTestResults
from app.database.redis.rs_test_result import mg_insert_test_result_done
from app.database.utils.output_strategy import OutputStrategy
from app.database.utils.what_strategy import WhatStrategy
from app.schema.campaign_schema import Scenario
from app.utils.pgdb import pool


def retrieve_tuple_data(
    result_date: datetime,
    project_name: str,
    version: str,
    campaign_id: int,
    rows: DictReader | List[dict],
    is_partial: bool,
    result: List[
        Tuple[
            datetime,
            str,
            str,
            int,
            int,
            int,
            int,
            str,
            bool,
        ],
    ],
) -> None:
    """:return list of tuple (date, str, str, int, int, int, int, str, bool)"""
    with pool.connection() as connection:
        connection.row_factory = dict_row
        for row in rows:
            if db_row := connection.execute(
                "select ep.id as epic_id, ft.id as feature_id,"
                " sc.id as scenario_internal_id from scenarios as sc "
                "inner join features as ft on sc.feature_id = ft.id "
                "inner join epics as ep on ep.id = ft.epic_id "
                "where ep.name = %s "
                "and ft.name = %s "
                "and sc.scenario_id = %s "
                "and ep.project_id = %s;",
                (
                    row["epic_id"],
                    row.get("feature_name", row.get("feature_id", None)),
                    row["scenario_id"],
                    project_name,
                ),
            ).fetchone():
                result.append(
                    (
                        result_date,
                        project_name,
                        version,
                        campaign_id,
                        db_row["epic_id"],
                        db_row["feature_id"],
                        db_row["scenario_internal_id"],
                        row["status"],
                        is_partial,
                    ),
                )


def check_result_uniqueness(
    project_name: str,
    version: str,
    result_date: datetime,
) -> None:
    """Check if result data exist for project_name-version-date exists
    :return None
    :raise DuplicateTestResults"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        if result := connection.execute(  # noqa: F841
            "select 0 from test_scenario_results where project_id = %s and version = %s and run_date = %s;",
            (
                project_name,
                version,
                result_date,
            ),
        ).fetchall():
            raise DuplicateTestResults(
                f"A test execution result exist for project '{project_name}'"
                f" in version '{version}' run at '{result_date}'"
            )


def set_status(
    current_status: str,
    new_result: str,
) -> str:
    """For container elements, set the status based on the worse status.
    i.e. container element is failed if one of its element is failed
    """
    if new_result == "failed" or current_status == "failed":
        return "failed"
    if new_result == "skipped" and current_status == "skipped":
        return "skipped"
    return "passed"


def __compute_epic_result(
    epic_list: list,
    current_epic: int,
    current_epic_status: str,
    result_epic: int,
    result_status: str,
    result_date: datetime,
    project_name: str,
    version: str,
    campaign_id: int,
    is_partial: bool,
) -> Tuple[int, str]:
    if current_epic != result_epic:
        epic_list.append(
            (
                result_date,
                project_name,
                version,
                campaign_id,
                current_epic,
                current_epic_status,
                is_partial,
            ),
        )
    return result_epic, set_status(
        current_epic_status,
        result_status,
    )


def __compute_feature_result(
    feature_list: list,
    current_feature: int,
    current_feature_status: str,
    result_feature: int,
    result_status: str,
    result_date: datetime,
    project_name: str,
    version: str,
    campaign_id: int,
    current_epic: int,
    is_partial: bool,
) -> Tuple[int, str]:
    if current_feature != result_feature:
        feature_list.append(
            (
                result_date,
                project_name,
                version,
                campaign_id,
                current_epic,
                current_feature,
                current_feature_status,
                is_partial,
            ),
        )
    return result_feature, set_status(
        current_feature_status,
        result_status,
    )


async def insert_result(
    result_date: datetime,
    project_name: str,
    version: str,
    campaign_id: int,
    is_partial: bool,
    mg_result_uuid: str,
    rows: DictReader | List[dict] | List[Scenario],
) -> None:
    """
    Insert campaign-occurrence results at the specific date
    Args:
        result_date: datetime, the results are observed
        project_name: str, the project to add results
        version: str, the project's version to add results
        campaign_id: int, the campaign internal id
        is_partial: bool, mark if the results are for specific tests (True) or whole test repository (False)
        mg_result_uuid: str, uuid of the task for reporting results
        rows: test results to compute

    Returns: None

    """
    results = []
    retrieve_tuple_data(
        result_date,
        project_name,
        version,
        campaign_id,
        rows,
        is_partial,
        results,
    )
    if not results:
        return mg_insert_test_result_done(
            key_uuid=mg_result_uuid,
            message="No result to record",
        )
    with pool.connection() as connection:
        with connection.cursor().copy(
            "COPY test_scenario_results (run_date, project_id, version,"
            " campaign_id, epic_id, feature_id, scenario_id,"
            " status, is_partial) from stdin"
        ) as copy:
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
                    is_partial,
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
                    is_partial,
                )

            # Last results
            features.append(
                (
                    result_date,
                    project_name,
                    version,
                    campaign_id,
                    current_epic,
                    current_feature,
                    current_feature_status,
                    is_partial,
                ),
            )
            epics.append(
                (
                    result_date,
                    project_name,
                    version,
                    campaign_id,
                    current_epic,
                    current_epic_status,
                    is_partial,
                ),
            )
        with connection.cursor().copy(
            "COPY test_feature_results (run_date, project_id, version,"
            " campaign_id, epic_id, feature_id,"
            " status, is_partial) from stdin"
        ) as copy:
            for feature in features:
                copy.write_row(feature)
        with connection.cursor().copy(
            "COPY test_epic_results (run_date, project_id, version,"
            " campaign_id, epic_id,"
            " status, is_partial) from stdin"
        ) as copy:
            for epic in epics:
                copy.write_row(epic)
    mg_insert_test_result_done(
        mg_result_uuid,
    )


class TestResults:
    def __init__(
        self: "TestResults",
        what: WhatStrategy,
        output: OutputStrategy,
    ) -> None:
        self.__what = what
        self.__output = output

    @property
    def what(self: "TestResults") -> WhatStrategy:
        return self.__what

    @what.setter
    def what(self: "TestResults", strategy: WhatStrategy) -> None:
        self.__what = strategy

    @property
    def output(self: "TestResults") -> OutputStrategy:
        return self.__output

    @output.setter
    def output(self: "TestResults", strategy: OutputStrategy) -> None:
        self.__output = strategy

    async def render(
        self: "TestResults",
        project_name: str,
        version: str,
        campaign_occurrence: str,
    ) -> str | dict:
        table_rows = await self.__what.gather(
            project_name,
            version,
            campaign_occurrence,
        )
        return await self.__output.render(
            table_rows=table_rows,
        )
