# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.conftest import error_message_extraction


class TestRestCampaign:
    project_name = "test_campaign"
    current_version = "1.0.0"

    def test_setup(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": TestRestCampaign.project_name},
            headers=logged,
        )
        assert response.status_code == 200
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/versions",
            json={"version": TestRestCampaign.current_version},
            headers=logged,
        )
        assert response.status_code == 200
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/versions/" f"{TestRestCampaign.current_version}/tickets",
            json={"reference": "ref-001", "description": "Description 1"},
            headers=logged,
        )
        assert response.status_code == 200
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/versions/" f"{TestRestCampaign.current_version}/tickets",
            json={"reference": "ref-002", "description": "Description 2"},
            headers=logged,
        )
        assert response.status_code == 200

    def test_get_campaigns(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns", headers=logged)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_campaigns_errors_404(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # project not found
        response = application.get(
            "/api/v1/projects/toto/campaigns",
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "'toto' is not registered"

        # version not found
        response = application.get(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
            params={"version": "3.0.0"},
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Version '3.0.0' is not found"

    def test_get_campaigns_errors_500(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.retrieve_campaign") as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_create_campaigns_errors_401(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
            json={"version": TestRestCampaign.current_version},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_create_campaigns(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
            json={"version": TestRestCampaign.current_version},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == {
            "project_name": TestRestCampaign.project_name,
            "version": TestRestCampaign.current_version,
            "occurrence": 1,
            "description": None,
            "status": "recorded",
        }

    payload_error_422 = [
        ({}, [{"loc": ["body", "version"], "msg": "Field required", "type": "missing"}]),
        (
            {"version": "1.1.1", "description": "desc"},
            [{"loc": ["body", "description"], "msg": "Extra inputs are not permitted", "type": "extra_forbidden"}],
        ),
    ]

    @pytest.mark.parametrize("payload,message", payload_error_422)
    def test_create_campaigns_errors_422(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        payload: dict,
        message: dict,
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
            json=payload,
            headers=logged,
        )
        assert response.status_code == 422
        assert error_message_extraction(response.json()["detail"]) == message

    def test_create_campaigns_errors_404_project(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            "/api/v1/projects/unknown_project/campaigns",
            json={"version": TestRestCampaign.current_version},
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "'unknown_project' is not registered"

    def test_create_campaigns_errors_404_version(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns", json={"version": "1.1.1"}, headers=logged
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Version '1.1.1' is not found"

    def test_create_campaigns_errors_500(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.create_campaign") as rp:
            rp.side_effect = Exception("error")
            response = application.post(
                f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                json={"version": TestRestCampaign.current_version},
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_fill_campaign_errors_401(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns" f"/{TestRestCampaign.current_version}/1",
            json={"version": TestRestCampaign.current_version},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_fill_campaign(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns" f"/{TestRestCampaign.current_version}/1",
            json={"ticket_reference": "ref-001"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == {"campaign_ticket_id": 1, "errors": []}

    def test_fill_campaign_200_no_error_on_duplicate(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns" f"/{TestRestCampaign.current_version}/1",
            json={"ticket_reference": "ref-001"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == {"campaign_ticket_id": 1, "errors": []}

    campaign_error_404 = [
        ("unknown_project", "1.0.0", 1, "ref-002", "'unknown_project' is not registered"),
        (project_name, "0.0.0", 1, "ref-002", "Version '0.0.0' is not found"),
        (project_name, current_version, 3, "ref-002", "Occurrence '3' not found"),
        (
            project_name,
            current_version,
            1,
            "ref-003",
            "Ticket 'ref-003' does not exist in project 'test_campaign' version '1.0.0'",
        ),
    ]

    @pytest.mark.parametrize("project,version,occurrence,ticket, message", campaign_error_404)
    def test_fill_campaign_errors_404(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project: str,
        version: str,
        occurrence: int,
        ticket: str,
        message: str,
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{project}/campaigns" f"/{version}/{occurrence}",
            json={"ticket_reference": ticket},
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_campaign(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/" f"{TestRestCampaign.current_version}/1",
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == {
            "description": None,
            "status": "recorded",
            "project_name": "test_campaign",
            "occurrence": 1,
            "version": "1.0.0",
            "tickets": [{"reference": "ref-001", "scenarios": [], "status": "open", "summary": "Description 1"}],
        }

    get_campaign_errors_404 = [
        ("unknown_project", "1.0.0", 1, "'unknown_project' is not registered"),
        (project_name, "0.0.0", 1, "Version '0.0.0' is not found"),
        (project_name, current_version, 3, "Occurrence '3' not found"),
    ]

    @pytest.mark.parametrize("project,version,occurrence,message", get_campaign_errors_404)
    def test_get_campaign_errors_404(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project: str,
        version: str,
        occurrence: int,
        message: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project}/campaigns/{version}/{occurrence}",
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_campaign_errors_500(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.get_campaign_content") as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/" f"{TestRestCampaign.current_version}/1",
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_patch_campaign_errors_401(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.patch(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/" f"{TestRestCampaign.current_version}/1",
            json={"status": "in progress", "description": "wonderful"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_patch_campaign(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.patch(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/" f"{TestRestCampaign.current_version}/1",
            json={"status": "in progress", "description": "wonderful"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == {
            "project_name": "test_campaign",
            "version": "1.0.0",
            "occurrence": 1,
            "description": "wonderful",
            "status": "in progress",
        }

    def test_patch_campaign_errors_422(
        self: "TestRestCampaign",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.patch(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/" f"{TestRestCampaign.current_version}/1",
            json={"status": "progress", "description": "wonderful"},
            headers=logged,
        )
        assert response.status_code == 422
        assert response.json()["detail"] == [
            {
                "ctx": {"expected": "'recorded', 'in progress', 'cancelled', 'done', 'closed' or " "'paused'"},
                "input": "progress",
                "loc": ["body", "status"],
                "msg": "Input should be 'recorded', 'in progress', 'cancelled', 'done', 'closed' " "or 'paused'",
                "type": "enum",
            }
        ]
