# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from typing import Any, Generator, List

from starlette.testclient import TestClient


def set_project(
    project_name: str,
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> None:
    """
    Create a new project
    Args:
        project_name: str
        application: Generator[TestClient, Any, None]
        logged: Generator[dict[str, str], Any, None]
    """
    response = application.post(
        "/api/v1/settings/projects",
        json={"name": project_name},
        headers=logged,
    )
    assert response.status_code == 200


def set_project_versions(
    project_name: str,
    versions: List[str],
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> None:
    """Create versions for a given project"""
    for version in versions:
        response = application.post(
            f"/api/v1/projects/{project_name}/versions",
            json={"version": version},
            headers=logged,
        )
        assert response.status_code == 200


def set_project_users(
    users: List[dict],
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> None:
    """Create or update users"""
    for user in users:
        response = application.post(
            "/api/v1/users",
            json=user,
            headers=logged,
        )
        if response.status_code == 409:
            response = application.patch(
                "/api/v1/users",
                json=user,
                headers=logged,
            )
            assert response.status_code == 200


def set_project_repository(
    project_name: str,
    repository_path: str,
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> None:
    """Create project test repository"""
    with open(repository_path, "rb") as file:
        response = application.post(
            f"/api/v1/projects/{project_name}/repository",
            files={"file": file},
            headers=logged,
        )
        assert response.status_code == 204


def set_project_tickets(
    project_name: str,
    tickets: List[dict],
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> None:
    """Create ticket"""
    for ticket in tickets:
        response = application.post(
            f"/api/v1/projects/{project_name}/versions/{ticket['version']}/tickets",
            json={"reference": ticket["reference"], "description": ticket["description"]},
            headers=logged,
        )
        assert response.status_code == 200


def set_project_campaign(
    project_name: str,
    version: str,
    tickets: List[dict],
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> int:
    """Create a campaign and link tickets"""
    response = application.post(
        f"/api/v1/projects/{project_name}/campaigns",
        json={"version": version},
        headers=logged,
    )
    assert response.status_code == 200
    __occurrence: int = response.json()["occurrence"]
    for ticket in tickets:
        response = application.put(
            f"/api/v1/projects/{project_name}/campaigns/{version}/{__occurrence}",
            json=ticket,
            headers=logged,
        )
        assert response.status_code == 200
    return __occurrence


def set_campaign_scenario_status(
    project_name: str,
    project_version: str,
    campaign_occurrence: int,
    scenario_status: List[dict],
    application: Generator[TestClient, Any, None],
    logged: Generator[dict[str, str], Any, None],
) -> None:
    """Set scenario status. Expecting key:
    - ticket_reference
    - scenario_id
    - feature_id
    - status
    """
    for sc in scenario_status:
        response = application.get(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}"
            f"/tickets/{sc["ticket_reference"]}",
            headers=logged,
        )
        assert response.status_code == 200
        __scenario_internal_id = None
        for _sc in response.json():
            if _sc["feature_id"] == sc["feature_id"] and _sc["scenario_id"] == sc["scenario_id"]:
                __scenario_internal_id = _sc["internal_id"]
        assert __scenario_internal_id is not None, "Cannot retrieve the scenario internal id"
        response = application.put(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}"
            f"/tickets/{sc["ticket_reference"]}/scenarios/{__scenario_internal_id}/status",
            params={"new_status": sc["status"]},
            headers=logged,
        )
