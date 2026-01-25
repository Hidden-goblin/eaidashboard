# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.schema.rest_enum import DeliverableTypeEnum
from app.utils.project_alias import provide
from tests.utils.project_setting import (
    set_campaign_scenario_status,
    set_project,
    set_project_campaign,
    set_project_repository,
    set_project_tickets,
    set_project_versions,
)


# noinspection PyUnresolvedReferences

PROJECT_NAME: str = "test_deliverables"
PROJECT_VERSION: str = "version 1.0"
PROJECT_CAMPAIGN_OCCURRENCE: int = 1
PROJECT_VERSION_TICKETS = [
    {"version": PROJECT_VERSION, "reference": "td-001", "description": "td-001"},
    {"version": PROJECT_VERSION, "reference": "td-002", "description": "td-002"},
    {"version": PROJECT_VERSION, "reference": "td-003", "description": "td-003"},
]

PROJECT_TEST_TICKET_SCENARIOS = [
    {
        "ticket_reference": "td-001",
        "scenarios": [
            {
                "scenario_id": "test_1",
                "epic": "first_epic",
                "feature_name": "New Test feature",
            },
            {
                "scenario_id": "test_2",
                "epic": "first_epic",
                "feature_name": "New Test feature",
            },
        ],
    },
    {
        "ticket_reference": "td-002",
        "scenarios": [{"scenario_id": "test_2", "epic": "first_epic", "feature_name": "Test feature"}],
    },
]
SCENARIOS_STATUS = [
    {
        "ticket_reference": "td-001",
        "scenario_id": "test_1",
        "feature_name": "New Test feature",
        "status": "in progress",
    },
    {
        "ticket_reference": "td-001",
        "scenario_id": "test_2",
        "feature_name": "New Test feature",
        "status": "waiting fix",
    },
    {
        "ticket_reference": "td-002",
        "scenario_id": "test_2",
        "feature_name": "Test feature",
        "status": "waiting answer",
    },
]


@pytest.fixture(scope="module", autouse=True)
def test_setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    set_project(
        PROJECT_NAME,
        application,
        logged_setting,
    )
    set_project_versions(
        PROJECT_NAME,
        [
            PROJECT_VERSION,
        ],
        application,
        logged_setting,
    )
    set_project_tickets(
        PROJECT_NAME,
        PROJECT_VERSION_TICKETS,
        application,
        logged_setting,
    )
    set_project_repository(
        PROJECT_NAME,
        "tests/resources/repository_as_csv_extended.csv",
        application,
        logged_setting,
    )


@pytest.fixture(scope="module")
def campaign_occurrence(application, logged_setting):
    yield set_project_campaign(
        PROJECT_NAME,
        PROJECT_VERSION,
        PROJECT_TEST_TICKET_SCENARIOS,
        application,
        logged_setting,
    )


@pytest.fixture(scope="module")
def campaign_scenario_status(application, logged_setting, campaign_occurrence):
    set_campaign_scenario_status(
        PROJECT_NAME,
        PROJECT_VERSION,
        campaign_occurrence,
        SCENARIOS_STATUS,
        application,
        logged_setting,
    )


def test_register_campaign_status(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text


campaign_error_404 = [
    ("unkown", PROJECT_VERSION, "valid"),
    (PROJECT_NAME, "v 9999", "valid"),
    (PROJECT_NAME, PROJECT_VERSION, "invalid"),
]


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type", campaign_error_404)
def test_register_campaign_status_error_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
    campaign_occurrence,
    project_name: str,
    project_version: str,
    campaign_occurrence_type: int,
) -> None:
    if campaign_occurrence_type == "valid":
        campaign_occurrence_value = campaign_occurrence
    else:
        campaign_occurrence_value = campaign_occurrence + 100
    response = application.post(
        f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence_value}",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_register_campaign_status_error_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
) -> None:
    with patch("app.routers.rest.project_campaigns.register_manual_campaign_result") as rp:
        rp.side_effect = Exception("Error")
        response = application.post(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
            f"/{campaign_occurrence}",
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_register_campaign_status_error_401(
    application: Generator[TestClient, Any, None],
        campaign_occurrence,
) -> None:
    application.cookies.set("access_token", "")
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}",
    )
    assert response.status_code == 401, response.text


def test_get_campaign_results(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence
) -> None:
    # Default
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}/deliverables",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert provide(PROJECT_NAME) in response.text

    # Existing file
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}/deliverables",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert provide(PROJECT_NAME) in response.text


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type", campaign_error_404)
def test_get_campaign_results_error_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
    project_name: str,
    project_version: str,
    campaign_occurrence_type: int,
) -> None:
    if campaign_occurrence_type == "valid":
        campaign_occurrence_value = campaign_occurrence
    else:
        campaign_occurrence_value = campaign_occurrence + 100
    response = application.get(
        f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence_value}/deliverables",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_get_campaign_results_error_401(
    application: Generator[TestClient, Any, None],
        campaign_occurrence,
) -> None:
    application.cookies.set("access_token", "")
    # Default
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}/deliverables",
    )
    assert response.status_code == 401, response.text


def test_get_campaign_results_error_422(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
) -> None:
    # Passing case
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}/deliverables",
        params={"deliverable_type": DeliverableTypeEnum.EVIDENCE.value, "ticket_ref": "td-001"},
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text

    # Error case
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}/deliverables",
        params={"deliverable_type": "test", "ticket_ref": "td-001"},
        headers=logged_setting,
    )
    assert response.status_code == 422, response.text


def test_get_campaign_results_error_404_specific(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
) -> None:
    # Passing case
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}/deliverables",
        params={"deliverable_type": DeliverableTypeEnum.EVIDENCE.value, "ticket_ref": "td-003"},
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_get_campaign_results_error_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
) -> None:
    with patch("app.routers.rest.project_campaigns.rs_retrieve_file") as rp:
        rp.side_effect = Exception("Error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
            f"/{campaign_occurrence}/deliverables",
            params={"deliverable_type": DeliverableTypeEnum.EVIDENCE.value, "ticket_ref": "td-001"},
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_get_asynchronous_status(
    application: Generator[TestClient, Any, None],
        logged_setting,
        campaign_occurrence,
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}"
        f"/{campaign_occurrence}",
        headers=logged_setting,
    )
    response = application.get(
        "/api/v1/status",
        params={"status_key": response.json()},
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
