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
class TestRestDeliverables:
    project_name: str = "test_deliverables"
    project_version: str = "version 1.0"
    project_campaign_occurrence: int = 1
    project_version_tickets = [
        {"version": project_version, "reference": "td-001", "description": "td-001"},
        {"version": project_version, "reference": "td-002", "description": "td-002"},
        {"version": project_version, "reference": "td-003", "description": "td-003"},
    ]

    project_test_ticket_scenarios = [
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
    scenarios_status = [
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

    def test_setup(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        set_project(
            TestRestDeliverables.project_name,
            application,
            logged,
        )
        set_project_versions(
            TestRestDeliverables.project_name,
            [
                TestRestDeliverables.project_version,
            ],
            application,
            logged,
        )
        set_project_tickets(
            TestRestDeliverables.project_name,
            TestRestDeliverables.project_version_tickets,
            application,
            logged,
        )
        set_project_repository(
            TestRestDeliverables.project_name,
            "tests/resources/repository_as_csv_extended.csv",
            application,
            logged,
        )
        TestRestDeliverables.project_campaign_occurrence = set_project_campaign(
            TestRestDeliverables.project_name,
            TestRestDeliverables.project_version,
            TestRestDeliverables.project_test_ticket_scenarios,
            application,
            logged,
        )

        set_campaign_scenario_status(
            TestRestDeliverables.project_name,
            TestRestDeliverables.project_version,
            TestRestDeliverables.project_campaign_occurrence,
            TestRestDeliverables.scenarios_status,
            application,
            logged,
        )

    def test_register_campaign_status(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}",
            headers=logged,
        )
        assert response.status_code == 200, response.text

    campaign_error_404 = [
        ("unkown", project_version, project_campaign_occurrence),
        (project_name, "v 9999", project_campaign_occurrence),
        (project_name, project_version, project_campaign_occurrence + 100),
    ]

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence", campaign_error_404)
    def test_register_campaign_status_error_404(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: int,
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_register_campaign_status_error_500(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.register_manual_campaign_result") as rp:
            rp.side_effect = Exception("Error")
            response = application.post(
                f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
                f"/{TestRestDeliverables.project_campaign_occurrence}",
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_register_campaign_status_error_401(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}",
        )
        assert response.status_code == 401, response.text

    def test_get_campaign_results(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Default
        response = application.get(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        assert provide(TestRestDeliverables.project_name) in response.text

        # Existing file
        response = application.get(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        assert provide(TestRestDeliverables.project_name) in response.text

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence", campaign_error_404)
    def test_get_campaign_results_error_404(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: int,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/deliverables",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_get_campaign_results_error_401(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
    ) -> None:
        # Default
        response = application.get(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
        )
        assert response.status_code == 401, response.text

    def test_get_campaign_results_error_422(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Passing case
        response = application.get(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
            params={"deliverable_type": DeliverableTypeEnum.EVIDENCE.value, "ticket_ref": "td-001"},
            headers=logged,
        )
        assert response.status_code == 200, response.text

        # Error case
        response = application.get(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
            params={"deliverable_type": "test", "ticket_ref": "td-001"},
            headers=logged,
        )
        assert response.status_code == 422, response.text

    def test_get_campaign_results_error_404_specific(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Passing case
        response = application.get(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
            params={"deliverable_type": DeliverableTypeEnum.EVIDENCE.value, "ticket_ref": "td-003"},
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_get_campaign_results_error_500(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.rs_retrieve_file") as rp:
            rp.side_effect = Exception("Error")
            response = application.get(
                f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
                f"/{TestRestDeliverables.project_campaign_occurrence}/deliverables",
                params={"deliverable_type": DeliverableTypeEnum.EVIDENCE.value, "ticket_ref": "td-001"},
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_get_asynchronous_status(
        self: "TestRestDeliverables",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestDeliverables.project_name}/campaigns/{TestRestDeliverables.project_version}"
            f"/{TestRestDeliverables.project_campaign_occurrence}",
            headers=logged,
        )
        response = application.get(
            "/api/v1/status",
            params={"status_key": response.json()},
            headers=logged,
        )
        assert response.status_code == 200, response.text
