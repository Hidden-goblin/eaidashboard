# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

import pytest
from starlette.testclient import TestClient

from tests.utils.project_setting import set_project_repository, set_project

PROJECT_NAME = "test_scenario_update"
SCENARIO = {
    "scenario_id": "test_1",
    "epic": "first_epic",
    "feature_name": "New Test feature",
    "name": "Generate report",
    "tags": "event, id=test_1",
    "steps": """Given I write a workflow reference
When I generate the report
Then The workflow picture is added"""
}


@pytest.fixture(scope="module", autouse=True)
def _setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    set_project(
        PROJECT_NAME,
        application,
        logged_setting,
    )
    set_project_repository(
        PROJECT_NAME,
        "tests/resources/repository_as_csv_feature_scenario_accross_files.csv",
        application,
        logged_setting,
    )


def test_update_scenario(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/New Test feature/scenarios/test_1",
        headers=logged_setting,
        json={"name": "New name", "tags": "new tags", "steps": "new steps"},
    )
    assert response.status_code == 204, response.text

    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/New Test feature/scenarios/test_1",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    scenario = response.json()
    assert scenario["name"] == "New name"
    assert scenario["tags"] == "new tags"
    assert scenario["steps"] == "new steps"


def test_update_scenario_not_found(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.put(
        "/api/v1/projects/default/epics/default/features/default/scenarios/not-found",
        headers=logged_setting,
        json={"name": "New name"},
    )
    assert response.status_code == 404, response.text


def test_update_scenario_no_auth(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/New Test feature/scenarios/test_1",
        json={"name": "New name"},
    )
    assert response.status_code == 401, response.text


def test_update_scenario_no_params(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/New Test feature/scenarios/test_1",
        headers=logged_setting,
        json={"test": "test"},
    )
    assert response.status_code == 422, response.text

    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features/New Test feature/scenarios/test_1",
        headers=logged_setting,
        json={},
    )
    assert response.status_code == 422, response.text
