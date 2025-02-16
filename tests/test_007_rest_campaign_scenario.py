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
class TestRestCampaignScenario:
    project_name: str = "test_campaign_scenario"
    project_version: str = "version 1.0"
    project_campaign_occurrence: int = 1
    project_version_tickets = [
        {"version": project_version, "reference": "tcs-001", "description": "tcs-001"},
        {"version": project_version, "reference": "tcs-002", "description": "tcs-002"},
    ]
    project_tickets = [
        {"ticket_reference": "tcs-001"},
        # {"ticket_reference": "tcs-002"},
    ]
    testing_repartition = {
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
    scenario_id = None

    def test_setup(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Create project
        set_project(
            TestRestCampaignScenario.project_name,
            application,
            logged,
        )
        # Upload scenarios
        set_project_versions(
            TestRestCampaignScenario.project_name,
            [
                TestRestCampaignScenario.project_version,
            ],
            application,
            logged,
        )
        set_project_repository(
            TestRestCampaignScenario.project_name,
            "tests/resources/repository_as_csv.csv",
            application,
            logged,
        )
        set_project_tickets(
            TestRestCampaignScenario.project_name,
            TestRestCampaignScenario.project_version_tickets,
            application,
            logged,
        )
        TestRestCampaignScenario.project_campaign_occurrence = set_project_campaign(
            TestRestCampaignScenario.project_name,
            TestRestCampaignScenario.project_version,
            TestRestCampaignScenario.project_tickets,
            application,
            logged,
        )

    def test_link_scenario_to_campaign_ticket(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            json=TestRestCampaignScenario.testing_repartition["tcs-001"],
            headers=logged,
        )
        assert response.status_code == 200, response.text

    def test_fill_campaign_with_ticket_and_scenario(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}",
            json={
                "ticket_reference": "tcs-002",
                "scenarios": [
                    {"scenario_id": "test_1", "epic": "first_epic", "feature_name": "New Test feature"},
                    {"scenario_id": "test_1", "epic": "first_epic", "feature_name": "Test feature"},
                ],
            },
            headers=logged,
        )
        assert response.status_code == 200, response.text
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-002",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        assert len(response.json()) == 2, response.text

    scenario_error_404 = [
        (
            "test_99",
            "first_epic",
            "New Test feature",
            [
                "Found 0 scenarios while expecting one and only one.\nSearch criteria was scenario_id='test_99'"
                " epic='first_epic' feature_name='New Test feature' filename=None"
            ],
        ),
        (
            "test_1",
            "cipe_tsrif",
            "New Test feature",
            [
                "Found 0 scenarios while expecting one and only one.\nSearch criteria was scenario_id='test_1'"
                " epic='cipe_tsrif' feature_name='New Test feature' filename=None"
            ],
        ),
        (
            "test_1",
            "first_epic",
            "NTf",
            [
                "Found 0 scenarios while expecting one and only one.\n"
                "Search criteria was scenario_id='test_1' epic='first_epic' feature_name='NTf' filename=None"
            ],
        ),
    ]

    @pytest.mark.parametrize("scenario_id,epic,feature_name,errors_message", scenario_error_404)
    def test_fill_campaign_with_ticket_and_scenario_bad_scenario(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        scenario_id: str,
        epic: str,
        feature_name: str,
        errors_message: List[str,],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}",
            json={
                "ticket_reference": "tcs-002",
                "scenarios": [{"scenario_id": scenario_id, "epic": epic, "feature_name": feature_name}],
            },
            headers=logged,
        )
        assert response.status_code == 200, response.text
        assert response.json()["errors"] == errors_message

    def test_fill_campaign_with_ticket_and_scenario_error_500(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.db_fill_campaign") as rp:
            rp.side_effect = Exception("error")
            response = application.put(
                f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
                f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}",
                json={
                    "ticket_reference": "tcs-002",
                    "scenarios": [{"scenario_id": "test_1", "epic": "first_epic", "feature_name": "New Test feature"}],
                },
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_retrieve_campaign_ticket(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets",
            headers=logged,
        )
        assert response.status_code == 200, response.text

    def test_retrieve_campaign_ticket_error_401(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets",
        )
        assert response.status_code == 401, response.text

    get_campaign_ticket_error_404 = [
        ("unkown", project_version, project_campaign_occurrence),
        (project_name, "version", project_campaign_occurrence),
        (project_name, project_version, 10),
    ]

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence", get_campaign_ticket_error_404)
    def test_retrieve_campaign_ticket_error_404(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/tickets",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_retrieve_campaign_ticket_error_500(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.db_get_campaign_tickets") as rp:
            rp.side_effect = Exception("Something went wrong")
            response = application.get(
                f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
                f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
                f"/tickets",
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_link_scenario_to_campaign_ticket_error_401(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            json=TestRestCampaignScenario.testing_repartition["tcs-001"],
        )
        assert response.status_code == 401

    link_error_404 = [
        ("unkown", project_version, project_campaign_occurrence, "tcs-001"),
        (project_name, "version", project_campaign_occurrence, "tcs-001"),
        (project_name, project_version, 10, "tcs-001"),
        (project_name, project_version, project_campaign_occurrence, "vvv-999"),
    ]

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence,ticket_ref", link_error_404)
    def test_link_scenario_to_campaign_ticket_error_404(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: int,
        ticket_ref: str,
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/tickets/{ticket_ref}",
            json=TestRestCampaignScenario.testing_repartition["tcs-001"],
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_link_scenario_to_campaign_ticket_error_500(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.db_put_campaign_ticket_scenarios") as rp:
            rp.side_effect = Exception("Error")
            response = application.put(
                f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
                f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
                f"/tickets/tcs-001",
                json=TestRestCampaignScenario.testing_repartition["tcs-001"],
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_get_campaign_ticket(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200, response.text

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence,ticket_ref", link_error_404)
    def test_get_campaign_ticket_error_404(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: int,
        ticket_ref: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project_name}/campaigns/{project_version}/{campaign_occurrence}/tickets/{ticket_ref}",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_get_campaign_ticket_error_401(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
        )
        assert response.status_code == 401, response.text

    def test_get_campaign_ticket_error_500(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.project_campaigns.db_get_campaign_ticket_scenarios") as rp:
            rp.side_effect = Exception("Error")
            response = application.get(
                f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
                f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
                f"/tickets/tcs-001",
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_get_campaign_ticket_scenario(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}",
            headers=logged,
        )
        assert response.status_code == 200, response.text

    def test_get_campaign_ticket_scenario_error_401(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"

        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}",
        )
        assert response.status_code == 401, response.text

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence,ticket_ref", link_error_404)
    def test_get_campaign_ticket_scenario_error_404(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: int,
        ticket_ref: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
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
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_get_campaign_ticket_scenario_error_500(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
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
                f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
                f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
                f"/tickets/tcs-001/scenarios/{__scenario_id}",
                headers=logged,
            )
            assert response.status_code == 500, response.text

    def test_update_scenario_status(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
            params={"new_status": "in progress"},
            headers=logged,
        )
        TestRestCampaignScenario.scenario_id = __scenario_id
        assert response.status_code == 200

    def test_scenario_status_update_is_done(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{TestRestCampaignScenario.scenario_id}",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "in progress", response.text

    def test_update_scenario_status_error_422(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
            params={"new_status": "unknown status"},
            headers=logged,
        )
        assert response.status_code == 422, response.text

    def test_update_scenario_status_error_401(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
            params={"new_status": "in progress"},
        )
        assert response.status_code == 401, response.text

    @pytest.mark.parametrize("project_name,project_version,campaign_occurrence,ticket_ref", link_error_404)
    def test_update_scenario_status_error_404(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        project_version: str,
        campaign_occurrence: int,
        ticket_ref: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
        response = application.put(
            f"/api/v1/projects/{project_name}/campaigns/"
            f"{project_version}/{campaign_occurrence}"
            f"/tickets/{ticket_ref}/scenarios/{__scenario_id}/status",
            params={"new_status": "in progress"},
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_update_scenario_status_error_404_specific(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200, response.text
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
        __scenario_id += 1000  # Change the id
        response = application.put(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
            params={"new_status": "in progress"},
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_update_scenario_status_error_500(
        self: "TestRestCampaignScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
            f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
            f"/tickets/tcs-001",
            headers=logged,
        )
        assert response.status_code == 200
        __scenario_id = None
        for _sc in response.json():
            if _sc["feature_name"] == "New Test feature":
                __scenario_id = _sc["scenario_tech_id"]
        assert __scenario_id is not None, "Cannot retrieve the scenario internal id"
        with patch("app.routers.rest.project_campaigns.db_set_campaign_ticket_scenario_status") as rp:
            rp.side_effect = Exception("Error")
            response = application.put(
                f"/api/v1/projects/{TestRestCampaignScenario.project_name}/campaigns/"
                f"{TestRestCampaignScenario.project_version}/{TestRestCampaignScenario.project_campaign_occurrence}"
                f"/tickets/tcs-001/scenarios/{__scenario_id}/status",
                params={"new_status": "in progress"},
                headers=logged,
            )
        assert response.status_code == 500, response.text
