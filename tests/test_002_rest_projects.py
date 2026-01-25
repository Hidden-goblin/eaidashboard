# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.conftest import status_404_error_message_check
from tests.utils.project_setting import set_project

# noinspection PyUnresolvedReferences


@pytest.fixture(autouse=True)
def _setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    for project in ["test", "test_users", "test_users2"]:
        set_project(project, application, logged_setting)
    application.cookies.set("access_token", "")
    yield

def test_get_projects(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        "/api/v1/projects",
        headers=logged_setting,
    )
    assert response.status_code == 200
    projects = [pjt["name"] for pjt in response.json()]
    # Inclusion assertion - created as prerequisite included in retrieved
    assert all(name in projects  for name in ["test", "test_users", "test_users2"]), f"Retrieved {projects}"


def test_get_projects_limit(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        "/api/v1/projects",
        params={"skip": 4, "limit": 2},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == []


limit_outbound = [(-4, -2, "OFFSET must not be negative"), (4, -2, "LIMIT must not be negative")]


@pytest.mark.parametrize("skip,limit,message", limit_outbound)
def test_get_projects_limit_outbound(
    application: Generator[TestClient, Any, None],
        logged_setting,
    skip: int,
    limit: int,
    message: str,
) -> None:
    response = application.get(
        "/api/v1/projects",
        params={"skip": skip, "limit": limit},
        headers=logged_setting,
    )
    assert response.status_code == 500
    assert response.json() == {"detail": message}


def test_get_projects_errors_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    with patch("app.routers.rest.projects.get_projects") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            "/api/v1/projects",
            headers=logged_setting,
        )
        assert response.status_code == 500


def test_get_one_project(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        "/api/v1/projects/test",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == {"archived": [], "current": [], "future": [], "name": "test"}


def test_get_one_projects_errors_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        "/api/v1/projects/unknown",
        headers=logged_setting,
    )
    status_404_error_message_check(response, "'unknown' is not registered")


def test_get_one_projects_errors_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    with patch("app.routers.rest.projects.get_project") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            "/api/v1/projects/test",
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "error"}


def test_create_version_errors_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.post(
        "/api/v1/projects/test/versions",
        json={"version": "1.0.0"},
    )
    assert response.status_code == 401


def test_create_version(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.post(
        "/api/v1/projects/test/versions",
        json={"version": "1.0.0"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert isinstance(response.json()["inserted_id"], int)


def test_create_version_errors_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.post(
        "/api/v1/projects/tests/versions",
        json={"version": "1.0.0"},
        headers=logged_setting,
    )
    status_404_error_message_check(response, "'tests' is not registered")


@pytest.mark.tags("error", "unique_constraint")
@pytest.mark.path("projects/versions")
@pytest.mark.test_steps(
    "Given projects 'test' has a version '1.0.0'",
    "When admin adds a version '1.0.0'",
    "Then admin gets a 409 error",
)
def test_create_version_errors_409(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.post(
        "/api/v1/projects/test/versions",
        json={"version": "1.0.0"},
        headers=logged_setting,
    )
    assert response.status_code == 409
    # TODO: Replace by Regex on text
    # assert response.json() == {
    #     "detail": "duplicate key value violates unique constraint"
    #     ' "unique_project_version"\nDETAIL:'
    #     "  Key (project_id, version)=(1, 1.0.0) already"
    #     " exists."
    # }


def test_create_version_errors_422(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.post(
        "/api/v1/projects/test/versions",
        json={"test": "1.0.0"},
        headers=logged_setting,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Field required"
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "version"]


def test_create_version_errors_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    with patch("app.routers.rest.version.create_project_version") as rp:
        rp.side_effect = Exception("error")
        response = application.post(
            "/api/v1/projects/test/versions",
            json={"version": "1.0.0"},
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "error"}


def test_update_version_errors_401(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.put(
        "/api/v1/projects/test/versions/1.0.0",
        json={"status": "cancelled"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    keys = ("version", "created", "updated", "started", "end_forecast", "status", "statistics", "bugs")

    assert all(key in response.json().keys() for key in keys)
    assert response.json()["status"] == "cancelled"
    # preparing other status
    response = application.post(
        "/api/v1/projects/test/versions",
        json={"version": "1.0.1"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    response = application.post("/api/v1/projects/test/versions", json={"version": "1.0.2"}, headers=logged_setting)
    assert response.status_code == 200
    response = application.put(
        "/api/v1/projects/test/versions/1.0.0",
        json={"status": "archived"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    response = application.put(
        "/api/v1/projects/test/versions/1.0.1",
        json={"status": "test plan writing"},
        headers=logged_setting,
    )
    assert response.status_code == 200


def test_get_one_project_with_version(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        "/api/v1/projects/test",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()["archived"]) == 1
    assert len(response.json()["current"]) == 1
    assert len(response.json()["future"]) == 1
    assert response.json()["archived"][0]["version"] == "1.0.0"
    assert response.json()["current"][0]["version"] == "1.0.1"
    assert response.json()["future"][0]["version"] == "1.0.2"


transition = [
    "test plan writing",
    "test plan sent",
    "test plan accepted",
    "campaign started",
    "campaign ended",
    "ter writing",
    "ter sent",
    "archived",
]


@pytest.mark.parametrize("status", transition)
def test_update_versions_transition(
    application: Generator[TestClient, Any, None],
        logged_setting,
    status: str,
) -> None:
    response = application.put("/api/v1/projects/test/versions/1.0.2", json={"status": status}, headers=logged_setting)
    assert response.status_code == 200
    assert response.json()["status"] == status


def test_update_versions_empty_payload(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.put(
        "/api/v1/projects/test/versions/1.0.2",
        json={},
        headers=logged_setting,
    )
    assert response.status_code == 200


update_errors = [
    ({"started": "2023:01:31"}, "time data '2023:01:31' does not match format '%Y-%m-%d'"),
    ({"end_forecast": "31-01-2023"}, "time data '31-01-2023' does not match format '%Y-%m-%d'"),
    ({"status": "unknown"}, "Status 'unknown' is not accepted"),
]


@pytest.mark.parametrize("payload,message", update_errors)
def test_update_versions_400(
    application: Generator[TestClient, Any, None],
        logged_setting,
    payload: dict,
    message: str,
) -> None:
    response = application.put(
        "/api/v1/projects/test/versions/1.0.2",
        json=payload,
        headers=logged_setting,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == message


def test_update_versions_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    with patch("app.routers.rest.version.update_version_data") as rp:
        rp.side_effect = Exception("error")
        response = application.put(
            "/api/v1/projects/test/versions/1.0.1",
            json={"status": "cancelled"},
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "error"}


def test_get_version(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    response = application.get(
        "/api/v1/projects/test/versions/1.0.1",
        headers=logged_setting,
    )
    assert response.status_code == 200
    keys = ("bugs", "statistics", "status", "version", "created", "updated")
    assert all(key in response.json().keys() for key in keys)
    assert response.json()["version"] == "1.0.1"
    assert response.json()["status"] == "test plan writing"


version_errors_404 = [
    ("toto", "1.0.1", "'toto' is not registered"),
    ("test", "2.0.0", "Version '2.0.0' is not found"),
]


@pytest.mark.parametrize("project,version,message", version_errors_404)
def test_get_version_errors_404(
    application: Generator[TestClient, Any, None],
        logged_setting,
    project: str,
    version: str,
    message: str,
) -> None:
    response = application.get(
        f"/api/v1/projects/{project}/versions/{version}",
        headers=logged_setting,
    )
    status_404_error_message_check(response, message)


def test_get_version_errors_500(
    application: Generator[TestClient, Any, None],
        logged_setting,
) -> None:
    with patch("app.routers.rest.version.get_version") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            "/api/v1/projects/test/versions/1.0.1",
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "error"}
