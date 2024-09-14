# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

import dpath
from starlette.testclient import TestClient


class TestRestCampaignWorkflow:
    project_name = "test_campaign_workflow"
    project_version = {"past": "0.9", "current": "1.0", "next": "1.1"}
    dev_tickets = {
        "first": {"reference": "ref-001", "description": "Description of first"},
        "second": {"reference": "ref-002", "description": "Description of second"},
        "third": {"reference": "ref-003", "description": "Description of third"},
    }

    def test_setup(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        # Create project
        response = application.post(
            "/api/v1/settings/projects", json={"name": TestRestCampaignWorkflow.project_name}, headers=logged
        )
        assert response.status_code == 200

        # Create versions
        for ver in TestRestCampaignWorkflow.project_version.values():
            response = application.post(
                f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/versions",
                json={"version": ver},
                headers=logged,
            )
            assert response.status_code == 200

        # Create test repository
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post(
                f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/repository",
                files={"file": file},
                headers=logged,
            )
            assert response.status_code == 204

        # Add development tickets
        for ticket in TestRestCampaignWorkflow.dev_tickets.values():
            response = application.post(
                f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/versions"
                f"/{TestRestCampaignWorkflow.project_version['current']}/tickets",
                json=ticket,
                headers=logged,
            )
            assert response.status_code == 200

        # Create campaign for current version
        response = application.post(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns",
            json={"version": TestRestCampaignWorkflow.project_version["current"]},
            headers=logged,
        )
        assert response.status_code == 200

        # Add ticket in campaign
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns"
            f"/{TestRestCampaignWorkflow.project_version['current']}/1",
            json={
                "ticket_reference": "ref-001",
                "scenarios": [
                    {"epic": "first_epic", "feature_name": "Test feature", "scenario_id": "test_1"},
                    {"epic": "first_epic", "feature_name": "New Test feature", "scenario_id": "test_1"},
                ],
            },
            headers=logged,
        )
        assert response.status_code == 200

        response = application.put(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns"
            f"/{TestRestCampaignWorkflow.project_version['current']}/1",
            json={
                "ticket_reference": "ref-002",
                "scenarios": [{"epic": "second_epic", "feature_name": "Test feature", "scenario_id": "t_test_1"}],
            },
            headers=logged,
        )
        assert response.status_code == 200

    def test_retrieve_campaign(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns"
            f"/{TestRestCampaignWorkflow.project_version['current']}/1/tickets",
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json()["project_name"] == TestRestCampaignWorkflow.project_name
        assert response.json()["version"] == TestRestCampaignWorkflow.project_version["current"]
        assert response.json()["occurrence"] == 1

        tickets = dpath.values(response.json(), "tickets/*/reference")
        assert all(item in tickets for item in ["ref-001", "ref-002"])

    # Process test, record bug, link test to bug
    def test_workflow_test_bug_link(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns"
            f"/{TestRestCampaignWorkflow.project_version['current']}/1/tickets/ref-002",
            headers=logged,
        )
        assert response.status_code == 200
        # Test scenario
        scenario_internal_id = dpath.get(response.json(), "*/internal_id")
        # Update status
        response = application.put(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns"
            f"/{TestRestCampaignWorkflow.project_version['current']}/1/tickets/ref-002"
            f"/scenarios/{scenario_internal_id}/status",
            headers=logged,
            params={"new_status": "waiting fix"},
        )
        assert response.status_code == 200
        response = application.get(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}/campaigns"
            f"/{TestRestCampaignWorkflow.project_version['current']}/1/tickets/ref-002"
            f"/scenarios/{scenario_internal_id}",
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "waiting fix"
        # Create bug

        # Link bug to scenario
