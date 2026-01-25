# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator, List
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.utils.project_setting import (
    set_project,
    set_project_campaign,
    set_project_repository,
    set_project_tickets,
    set_project_versions,
)

# noinspection PyUnresolvedReferences

PROJECT_NAME: str = "test_campaign_scenario"
PROJECT_VERSION: str = "version 1.0"

PROJECT_VERSION_TICKETS = [
    {"version": PROJECT_VERSION, "reference": "tcs-001", "description": "tcs-001"},
    {"version": PROJECT_VERSION, "reference": "tcs-002", "description": "tcs-002"},
]
PROJECT_TICKETS = [
    {"ticket_reference": "tcs-001"},
    # {"ticket_reference": "tcs-002"},
]
TESTING_REPARTITION = {
    "tcs-001": [
        {
            "epic": "first_epic",  # First scenario
            "feature_name": "New Test feature",
            "scenario_ids": [
                "test_1",
            ],
        },
        {"epic": "first_epic", "feature_name": "Test feature", "scenario_ids": ["test_1"]},
    ]
}
SCENARIO_ID = None


@pytest.fixture(scope="module", autouse=True)
def _setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    # Create project
    set_project(
        PROJECT_NAME,
        application,
        logged_setting,
    )
    # Upload scenarios
    set_project_versions(
        PROJECT_NAME,
        [
            PROJECT_VERSION,
        ],
        application,
        logged_setting,
    )
    set_project_repository(
        PROJECT_NAME,
        "tests/resources/repository_as_csv.csv",
        application,
        logged_setting,
    )
    set_project_tickets(
        PROJECT_NAME,
        PROJECT_VERSION_TICKETS,
        application,
        logged_setting,
    )
    context_manager.set_context(
        "campaign_occurrence",
        set_project_campaign(
            PROJECT_NAME,
            PROJECT_VERSION,
            PROJECT_TICKETS,
            application,
            logged_setting,
        ),
    )
    application.cookies.set("access_token", "")
    yield
    context_manager.reset()


def test_validate_setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"api/v1/projects/{PROJECT_NAME}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text

    response = application.get(
        f"api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    print(response.text)

    response = application.get(
        f"api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "scenarios"},
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    print(response.text)


def test_link_scenario_to_campaign_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        json=TESTING_REPARTITION["tcs-001"],
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text


def test_fill_campaign_with_ticket_and_scenario(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}",
        json={
            "ticket_reference": "tcs-002",
            "scenarios": [
                {"scenario_id": "test_1", "epic": "first_epic", "feature_name": "New Test feature"},
                {"scenario_id": "test_1", "epic": "first_epic", "feature_name": "Test feature"},
            ],
        },
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-002",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2, response.text


scenario_error_404 = [
    (
        "test_99",
        "first_epic",
        "New Test feature",
        {"not_found_scenario": ["test_99"]},
    ),
    (
        "test_1",
        "cipe_tsrif",
        "New Test feature",
        {"not_found_scenario": ["test_1"]},
    ),
    (
        "test_1",
        "first_epic",
        "NTf",
        {"not_found_scenario": ["test_1"]},
    ),
]


@pytest.mark.parametrize("scenario_id,epic,feature_name,errors_message", scenario_error_404)
def test_fill_campaign_with_ticket_and_scenario_bad_scenario(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
    scenario_id: str,
    epic: str,
    feature_name: str,
    errors_message: List[str,],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}",
        json={
            "ticket_reference": "tcs-002",
            "scenarios": [{"scenario_id": scenario_id, "epic": epic, "feature_name": feature_name}],
        },
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert response.json().get("raw_data", "") == errors_message, response.text


def test_fill_campaign_with_ticket_and_scenario_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    with patch("app.routers.rest.project_campaigns.db_fill_campaign") as rp:
        rp.side_effect = Exception("error")
        response = application.put(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}",
            json={
                "ticket_reference": "tcs-002",
                "scenarios": [{"scenario_id": "test_1", "epic": "first_epic", "feature_name": "New Test feature"}],
            },
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_retrieve_campaign_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text


def test_retrieve_campaign_ticket_error_401(
    application: Generator[TestClient, Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets",
    )
    assert response.status_code == 401, response.text


get_campaign_ticket_error_404 = [
    ("unkown", PROJECT_VERSION, "valid"),
    (PROJECT_NAME, "version", "valid"),
    (PROJECT_NAME, PROJECT_VERSION, "invalid"),
]


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type", get_campaign_ticket_error_404)
def test_retrieve_campaign_ticket_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
    project_name: str,
    project_version: str,
    campaign_occurrence_type: str,
) -> None:
    if campaign_occurrence_type == "valid":
        campaign_occurrence = context_manager.get_context("campaign_occurrence")
    else:
        campaign_occurrence = "37"
    response = application.get(
        f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/tickets",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_retrieve_campaign_ticket_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    with patch("app.routers.rest.project_campaigns.db_get_campaign_tickets") as rp:
        rp.side_effect = Exception("Something went wrong")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets",
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_link_scenario_to_campaign_ticket_error_401(
    application: Generator[TestClient, Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        json=TESTING_REPARTITION["tcs-001"],
    )
    assert response.status_code == 401


link_error_404 = [
    ("unkown", PROJECT_VERSION, "valid", "tcs-001"),
    (PROJECT_NAME, "version", "valid", "tcs-001"),
    (PROJECT_NAME, PROJECT_VERSION, "invalid", "tcs-001"),
    (PROJECT_NAME, PROJECT_VERSION, "valid", "vvv-999"),
]


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type,ticket_ref", link_error_404)
def test_link_scenario_to_campaign_ticket_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
    project_name: str,
    project_version: str,
    campaign_occurrence_type: int,
    ticket_ref: str,
) -> None:
    if campaign_occurrence_type == "valid":
        campaign_occurrence = context_manager.get_context("campaign_occurrence")
    else:
        campaign_occurrence = "37"
    response = application.put(
        f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/tickets/{ticket_ref}",
        json=TESTING_REPARTITION["tcs-001"],
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_link_scenario_to_campaign_ticket_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    with patch("app.routers.rest.project_campaigns.db_put_campaign_ticket_scenarios") as rp:
        rp.side_effect = Exception("Error")
        response = application.put(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
            f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
            f"/tickets/tcs-001",
            json=TESTING_REPARTITION["tcs-001"],
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_get_campaign_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type,ticket_ref", link_error_404)
def test_get_campaign_ticket_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
    project_name: str,
    project_version: str,
    campaign_occurrence_type: int,
    ticket_ref: str,
) -> None:
    if campaign_occurrence_type == "valid":
        campaign_occurrence = context_manager.get_context("campaign_occurrence")
    else:
        campaign_occurrence = "37"
    response = application.get(
        f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/tickets/{ticket_ref}",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_get_campaign_ticket_error_401(
    application: Generator[TestClient, Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
    )
    assert response.status_code == 401, response.text


def test_get_campaign_ticket_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    with patch("app.routers.rest.project_campaigns.db_get_campaign_ticket_scenarios") as rp:
        rp.side_effect = Exception("Error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
            f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
            f"/tickets/tcs-001",
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_get_campaign_ticket_scenario(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text


def test_get_campaign_ticket_scenario_error_401(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
    application.cookies.set("access_token", "")
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}",
    )
    assert response.status_code == 401, response.text


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type,ticket_ref", link_error_404)
def test_get_campaign_ticket_scenario_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
    project_name: str,
    project_version: str,
    campaign_occurrence_type: int,
    ticket_ref: str,
) -> None:
    if campaign_occurrence_type == "valid":
        campaign_occurrence = context_manager.get_context("campaign_occurrence")
    else:
        campaign_occurrence = "37"
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    response = application.get(
        f"/api/v1/projects/{project_name}/campaigns/"
        f"{project_version}/{campaign_occurrence}"
        f"/tickets/{ticket_ref}/scenarios/{__scenario_id}",
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_get_campaign_ticket_scenario_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    with patch("app.routers.rest.project_campaigns.db_get_campaign_ticket_scenario") as rp:
        rp.side_effect = Exception("Error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
            f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}",
            headers=logged_setting,
        )
        assert response.status_code == 500, response.text


def test_update_scenario_status(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/"
        f"{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
        params={"new_status": "in progress"},
        headers=logged_setting,
    )
    assert response.status_code == 200


def test_scenario_status_update_is_done(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    # Prepare
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/"
        f"{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    # Act
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "in progress", response.text


def test_update_scenario_status_error_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    # Prepare
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/"
        f"{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    # Act
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
        params={"new_status": "unknown status"},
        headers=logged_setting,
    )
    assert response.status_code == 422, response.text


def test_update_scenario_status_error_401(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    # Prepare
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
    application.cookies.set("access_token", "")
    # Act
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
        params={"new_status": "in progress"},
    )
    assert response.status_code == 401, response.text


@pytest.mark.parametrize("project_name,project_version,campaign_occurrence_type,ticket_ref", link_error_404)
def test_update_scenario_status_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
    project_name: str,
    project_version: str,
    campaign_occurrence_type: int,
    ticket_ref: str,
) -> None:
    # Prepare

    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
    if campaign_occurrence_type == "valid":
        campaign_occurrence = context_manager.get_context("campaign_occurrence")
    else:
        campaign_occurrence = "37"
    # Act
    response = application.put(
        f"/api/v1/projects/{project_name}/campaigns/"
        f"{project_version}/{campaign_occurrence}"
        f"/tickets/{ticket_ref}/scenarios/{__scenario_id}/status",
        params={"new_status": "in progress"},
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_update_scenario_status_error_404_specific(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    # Prepare
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/"
        f"{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    # Act
    __scenario_id += 1000  # Change the id
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
        f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
        f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
        params={"new_status": "in progress"},
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text


def test_update_scenario_status_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    context_manager,  # noqa: ANN001
) -> None:
    # Prepare
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/campaigns/{PROJECT_VERSION}/"
        f"{context_manager.get_context('campaign_occurrence')}/tickets/tcs-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    __scenario_id = None
    for _sc in response.json():
        if _sc["feature_name"] == "New Test feature":
            __scenario_id = _sc["scenario_tech_id"]
    assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

    # Act
    with patch("app.routers.rest.project_campaigns.db_set_campaign_ticket_scenario_status") as rp:
        rp.side_effect = Exception("Error")
        response = application.put(
            f"/api/v1/projects/{PROJECT_NAME}/campaigns/"
            f"{PROJECT_VERSION}/{context_manager.get_context('campaign_occurrence')}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
            params={"new_status": "in progress"},
            headers=logged_setting,
        )
    assert response.status_code == 500, response.text
