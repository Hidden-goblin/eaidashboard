# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from csv import DictReader
from datetime import datetime
from io import StringIO
from typing import List, Tuple

from app.app_exception import IncorrectFieldsRequest, MalformedCsvFile
from app.database.postgre.pg_campaigns_management import create_campaign, retrieve_campaign_id
from app.database.postgre.pg_test_results import check_result_uniqueness
from app.database.postgre.testcampaign import db_get_campaign_scenarios
from app.database.redis.rs_test_result import mg_insert_test_result
from app.schema.campaign_followup_schema import ComputeResultSchema
from app.schema.campaign_schema import Scenario
from app.schema.error_code import ApplicationError
from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum, TestResultStatusEnum


async def insert_result(
    project_name: str,
    version: str,
    result_date: datetime,
    is_partial: bool,
    csv_file_content: str,
    part_of_campaign_occurrence: str = None,
) -> Tuple[str, int, DictReader]:
    """Check csv result format for insertion."""
    # SPEC: CSV file must contain the following field: project_id, epic_id, feature_name,
    # scenario_id, status
    buffer = StringIO(csv_file_content)
    rows = DictReader(buffer)
    expected_headers = (
        "epic_id",
        "feature_name",
        "scenario_id",
        "status",
    )
    oracle = [header not in rows.fieldnames for header in expected_headers]
    if any(oracle):
        raise MalformedCsvFile(
            f"The csv file misses some headers\n Missing header is True\n "
            f"{''.join([str(item) for item in zip(expected_headers, oracle)])}"
        )
    # SPEC: Check that a test result does not exist for the project_name, version, result_date tuple
    # for complete run
    if not is_partial:
        check_result_uniqueness(
            project_name,
            version,
            result_date,
        )
        campaign = await create_campaign(
            project_name,
            version,
            CampaignStatusEnum.closed,
        )
        campaign_id = await retrieve_campaign_id(
            project_name,
            version,
            campaign["occurrence"],
        )

    elif part_of_campaign_occurrence is None:
        raise IncorrectFieldsRequest("campaign_occurrence is mandatory for partial results")
    else:
        campaign_id = await retrieve_campaign_id(
            project_name,
            version,
            part_of_campaign_occurrence,
        )
    campaign_id = campaign_id.campaign_id
    # SPEC: Record an entry into mongo testResults and return entry uuid while importing data
    test_result_uuid = mg_insert_test_result(
        project_name,
        version,
        campaign_id,
        is_partial,
    )

    return test_result_uuid, campaign_id, rows


def __convert_scenario_status_to_three_state(
    scenarios: List[Scenario],
) -> None:
    """Map the scenario statuses to the 3 states passed/failed/skipped
    Is mocked by tests/test_10_rest_campaign_workflow.py:465
    for test
     tests.test_100_rest_campaign_workflow.TestRestCampaignWorkflow.test_test_manager_report_campaign_advancement
    """
    for scenario in scenarios:
        match scenario.status:
            case ScenarioStatusEnum.done:
                scenario.status = TestResultStatusEnum.passed
            case ScenarioStatusEnum.waiting_fix:
                scenario.status = TestResultStatusEnum.failed
            case _:
                scenario.status = TestResultStatusEnum.skipped


async def register_manual_campaign_result(
    project_name: str,
    version: str,
    campaign_occurrence: str,
) -> ComputeResultSchema | ApplicationError:
    """:return test_result_uuid, campaign_id, list of scenarios"""
    campaign_id_status = await retrieve_campaign_id(
        project_name,
        version,
        campaign_occurrence,
    )
    if isinstance(campaign_id_status, ApplicationError):
        return campaign_id_status
    test_result_uuid = mg_insert_test_result(
        project_name,
        version,
        campaign_id_status.campaign_id,
        True,
    )
    scenarios = db_get_campaign_scenarios(campaign_id_status.campaign_id)
    __convert_scenario_status_to_three_state(scenarios)
    return ComputeResultSchema(
        result_uuid=test_result_uuid, campaign_id=campaign_id_status.campaign_id, scenarios=scenarios
    )
