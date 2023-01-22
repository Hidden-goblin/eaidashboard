# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from csv import DictReader
from io import StringIO

from app.app_exception import IncorrectFieldsRequest, MalformedCsvFile
from app.database.mongo.mg_test_results import mg_insert_test_result
from app.database.postgre.pg_campaigns_management import create_campaign, retrieve_campaign_id
from app.database.postgre.pg_test_results import check_result_uniqueness
from app.schema.postgres_enums import CampaignStatusEnum


async def insert_result(project_name,
                        version,
                        result_date,
                        is_partial,
                        content,
                        part_of_campaign_occurrence: str = None
                        ):
    # SPEC: CSV file must contain the following field: project_id, epic_id, feature_name,
    # scenario_id, status
    buffer = StringIO(content)
    rows = DictReader(buffer)
    expected_headers = ("project_id",
                        "epic_id",
                        "feature_name",
                        "scenario_id",
                        "status")
    oracle = [header not in rows.fieldnames for header in expected_headers]
    if any(oracle):
        raise MalformedCsvFile(f"The csv file misses some headers\n Missing header is True\n "
                               f"{''.join([str(item) for item in zip(expected_headers, oracle)])}")
    # SPEC: Check that a test result does not exist for the project_name, version, result_date tuple
    # for complete run
    if not is_partial:
        check_result_uniqueness(project_name, version, result_date)
        campaign = await create_campaign(project_name, version, CampaignStatusEnum.closed)
        campaign_id = await retrieve_campaign_id(project_name,
                                                 version,
                                                 campaign["occurrence"])

    elif part_of_campaign_occurrence is None:
        raise IncorrectFieldsRequest("campaign_occurrence is mandatory for partial results")
    else:
        campaign_id = await retrieve_campaign_id(project_name,
                                                 version,
                                                 part_of_campaign_occurrence)
    campaign_id = campaign_id[0]
    # SPEC: Record an entry into mongo testResults and return entry uuid while importing data
    test_result_uuid = await mg_insert_test_result(project_name, version, campaign_id, is_partial)

    return test_result_uuid, campaign_id, rows
