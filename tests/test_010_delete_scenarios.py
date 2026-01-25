# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

import dpath
import pytest
from starlette.testclient import TestClient

from tests.utils.context_manager import Context
from tests.utils.project_setting import (
    set_campaign_scenario_status,
    set_project,
    set_project_campaign,
    set_project_repository,
    set_project_tickets,
    set_project_versions,
)


# noinspection PyUnresolvedReferences

PROJECT_NAME: str = "test_delete_scenario"
CURRENT_VERSION: str = "version 1.0"
NEXT_VERSION: str = "version 2.0"

PROJECT_VERSION_TICKETS = [
    {"version": CURRENT_VERSION, "reference": "tds-001", "description": "tds-001"},
    {"version": CURRENT_VERSION, "reference": "tds-002", "description": "tds-002"},
    {"version": NEXT_VERSION, "reference": "tds-003", "description": "tds-003"},
]

PROJECT_TEST_TICKET_SCENARIOS = [
    {
        "ticket_reference": "tds-001",
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
        "ticket_reference": "tds-002",
        "scenarios": [
            {
                "scenario_id": "test_2",
                "epic": "first_epic",
                "feature_name": "Test feature",
            },
        ],
    },
]
SCENARIOS_STATUS = [
    {
        "ticket_reference": "tds-001",
        "scenario_id": "test_1",
        "feature_name": "New Test feature",
        "status": "in progress",
    },
    {
        "ticket_reference": "tds-001",
        "scenario_id": "test_2",
        "feature_name": "New Test feature",
        "status": "waiting fix",
    },
    {
        "ticket_reference": "tds-002",
        "scenario_id": "test_2",
        "feature_name": "Test feature",
        "status": "waiting answer",
    },
]

@pytest.fixture(scope="module", autouse=True)
def test_setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
        context_manager,
) -> None:
    set_project(
        PROJECT_NAME,
        application,
        logged_setting,
    )
    set_project_versions(
        PROJECT_NAME,
        [
            CURRENT_VERSION,
            NEXT_VERSION,
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
        "tests/resources/repository_as_csv_feature_scenario_accross_files.csv",
        application,
        logged_setting,
    )
    context_manager.set_context(
        f"campaign/{CURRENT_VERSION}/occurrence",
        set_project_campaign(
            PROJECT_NAME,
            CURRENT_VERSION,
            PROJECT_TEST_TICKET_SCENARIOS,
            application,
            logged_setting,
        ),
    )

    set_campaign_scenario_status(
        PROJECT_NAME,
        CURRENT_VERSION,
        context_manager.get_context(f"campaign/{CURRENT_VERSION}/occurrence"),
        SCENARIOS_STATUS,
        application,
        logged_setting,
    )

@pytest.fixture()
def scenario_tech_id(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/"
        f"features/Test feature/scenarios/t_test_1",
        headers=logged_setting,
    )
    assert response.status_code == 200, f"{response.text}, {logged_setting}"

    yield response.json()["scenario_tech_id"]


def test_get_scenarios_from_feature(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/features/Test feature/scenarios",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text


def test_get_scenarios_from_feature_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    application.cookies.set("access_token", "")
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/features/Test feature/scenarios",
    )
    assert response.status_code == 401, response.text


project_epic_feature_not_found = [
    (PROJECT_NAME, "second_epic", "unknown"),
    (PROJECT_NAME, "unknown", "Test feature"),
    ("unknown", "second_epic", "Test feature"),
]


@pytest.mark.parametrize("project_name,epic_ref,feature_ref", project_epic_feature_not_found)
def test_get_scenarios_from_feature_error_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
    project_name: str,
    epic_ref: str,
    feature_ref: str,
) -> None:
    response = application.get(
        f"/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_get_scenario_from_feature_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    application.cookies.set("access_token", "")
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/"
        f"features/Test feature/scenarios/t_test_1",
    )
    assert response.status_code == 401, response.text


project_epic_feature_scenario_not_found = [
    (PROJECT_NAME, "second_epic", "unknown", "t_test_1"),
    (PROJECT_NAME, "unknown", "Test feature", "t_test_1"),
    ("unknown", "second_epic", "Test feature", "t_test_1"),
    (PROJECT_NAME, "second_epic", "Test feature", "unknown"),
]


@pytest.mark.parametrize("project_name,epic_ref,feature_ref,scenario_ref", project_epic_feature_scenario_not_found)
def test_get_scenario_from_feature_error_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
    project_name: str,
    epic_ref: str,
    feature_ref: str,
    scenario_ref: str,
) -> None:
    response = application.get(
        f"/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios/{scenario_ref}",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text




def test_get_scenario_from_feature_with_tech_id(
    application: Generator[TestClient, Any, None],
        logged_setting,
        scenario_tech_id,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/"
        f"features/Test feature"
        f"/scenarios/{scenario_tech_id}",
        headers=logged_setting,
        params={"technicalId": True},
    )
    assert response.status_code == 200, response.text
    assert response.json()["scenario_id"] == "t_test_1", response.text


def test_get_scenario_from_feature_with_tech_id_error_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/features/Test feature/scenarios/10000",
        headers=logged_setting,
        params={"technicalId": True},
    )
    assert response.status_code == 404, response.text


@pytest.mark.parametrize("project_name,epic_ref,feature_ref,scenario_ref", project_epic_feature_scenario_not_found)
def test_delete_scenario_error_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
    project_name: str,
    epic_ref: str,
    feature_ref: str,
    scenario_ref: str,
) -> None:
    response = application.delete(
        f"/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios/{scenario_ref}",
        headers=logged_setting,
    )

    assert response.status_code == 404, response.text


def test_delete_scenario_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    application.cookies.set("access_token", "")
    response = application.delete(
        f"/api/v1/projects/{PROJECT_NAME}/epics/second_epic/"
        f"features/Test feature/scenarios/t_test_1",
    )

    assert response.status_code == 401, response.text


def test_delete_scenario(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.delete(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/Test feature/scenarios/test_2",
        headers=logged_setting,
    )

    assert response.status_code == 204, response.text


def test_deleted_scenario_cannot_be_requested(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    # Deleted scenario cannot be requested repository, feature' scenarios
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/Test feature/scenarios/test_2",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_deleted_scenario_cannot_be_in_new_campaign(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    # Deleted scenario cannot be added to new campaign
    # Create new occurrence
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns",
        json={"version": CURRENT_VERSION},
        headers=logged_setting,
    )
    _occurrence: int = response.json()["occurrence"]

    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{CURRENT_VERSION}/{_occurrence}",
        json=PROJECT_TEST_TICKET_SCENARIOS[1],
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert dpath.get(response.json(), "raw_data/not_found_scenario") == ["test_2"], response.text


def test_deleted_scenario_appear_on_existing_campaign(
    application: Generator[TestClient, Any, None],
        logged_setting,
        context_manager,
) -> None:
    _occurrence = context_manager.get_context(f"campaign/{CURRENT_VERSION}/occurrence")
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{CURRENT_VERSION}/{_occurrence}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert (
        dpath.search(
            response.json(),
            "tickets/*/scenarios/*/name",
            afilter=lambda x: str(x) == "test_2",
        )
        is not None
    ), response.text
    # Deleted scenario appear on existing campaign
