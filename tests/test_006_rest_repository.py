# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

import pytest
from starlette.testclient import TestClient

from tests.utils.context_manager import Context
from tests.utils.project_setting import set_project

# noinspection PyUnresolvedReferences

PROJECT_NAME = "test_repository"
SECOND_PROJECT_NAME = "test.repository"
context = Context()


@pytest.fixture(autouse=True, scope="module")
def test_setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    """setup any state specific to the execution of the given class (which
    usually contains tests).
    """
    set_project(
        PROJECT_NAME,
        application,
        logged_setting,
    )
    set_project(
        SECOND_PROJECT_NAME,
        application,
        logged_setting,
    )
    application.cookies.set("access_token", "")
    yield


def test_upload_repository(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with open("tests/resources/repository_as_csv.csv", "rb") as file:
        response = application.post(
            f"/api/v1/projects/{PROJECT_NAME}/repository",
            files={"file": file},
            headers=logged_setting,
        )
        assert response.status_code == 204
        response = application.post(
            f"/api/v1/projects/{SECOND_PROJECT_NAME}/repository",
            files={"file": file},
            headers=logged_setting,
        )
        assert response.status_code == 204


def test_upload_repository_error_404_project_not_found(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with open("tests/resources/repository_as_csv.csv", "rb") as file:
        response = application.post(
            "/api/v1/projects/unknown/repository",
            files={"file": file},
            headers=logged_setting,
        )
        assert response.status_code == 404


def test_upload_repository_error_400_malformed_csv(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with open("tests/resources/repository_as_csv_malformed.csv", "rb") as file:
        response = application.post(
            f"/api/v1/projects/{PROJECT_NAME}/repository", files={"file": file}, headers=logged_setting
        )
        assert response.status_code == 400


def test_upload_repository_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    with open("tests/resources/repository_as_csv.csv", "rb") as file:
        response = application.post(f"/api/v1/projects/{PROJECT_NAME}/repository", files={"file": file})
        assert response.status_code == 401


def test_retrieve_repository(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(f"/api/v1/projects/{PROJECT_NAME}/repository", headers=logged_setting)
    assert response.status_code == 200


def test_retrieve_repository_all_features(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "features"},
        headers=logged_setting,
    )
    assert response.status_code == 200


def test_retrieve_repository_specific_features(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "features", "epic": "first_epic"},
        headers=logged_setting,
    )
    assert response.status_code == 200


def test_retrieve_repository_non_existing_specific_features(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "features", "epic": "first_epc"},
        headers=logged_setting,
    )
    assert response.status_code == 404, f"Expecting status code '404', get '{response.status_code}'"
    assert response.json() == {"detail": "Epic 'first_epc' not found in project 'test_repository'."}


def test_retrieve_repository_all_scenarios(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "scenarios"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) != 0


def test_retrieve_repository_epic_specific_scenarios(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "scenarios", "epic": "first_epic"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) != 0


def test_retrieve_repository_feature_specific_scenarios(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "scenarios", "feature": "New Test feature"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) != 0


def test_retrieve_repository_feature_specific_scenarios_case_sensitive(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/repository",
        params={"elements": "scenarios", "feature": "new test feature"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_retrieve_repository_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get("/api/v1/projects/unknown/repository", headers=logged_setting)
    assert response.status_code == 404


def test_retrieve_repository_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.get(f"/api/v1/projects/{PROJECT_NAME}/repository")
    assert response.status_code == 401


def test_retrieve_epics(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(f"/api/v1/projects/{PROJECT_NAME}/epics", headers=logged_setting)
    assert response.status_code == 200
    assert all(item in ["first_epic", "second_epic"] for item in response.json())


def test_retrieve_epics_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        "/api/v1/projects/unknown/epics",
        headers=logged_setting,
    )
    assert response.status_code == 404


def test_retrieve_features(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epic/features",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) == 2, (
        f"Should retrieve 2 features but get '{len(response.json())} from response\n {response.text}"
    )


def test_retrieve_features_error_404_project(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        "/api/v1/projects/unknown/epics/first_epic/features",
        headers=logged_setting,
    )
    assert response.status_code == 404


def test_retrieve_features_unknown_epic(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/epics/first_epc/features",
        headers=logged_setting,
    )
    assert response.status_code == 404, f"Expecting status code 404, get {response.status_code}"
    assert response.json() == {"detail": "Epic 'first_epc' not found in project 'test_repository'."}
