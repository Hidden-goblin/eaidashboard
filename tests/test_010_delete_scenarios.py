# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

import pytest
import dpath
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
class TestDeleteScenario:
    project_name: str = "test_delete_scenario"
    current_version: str = "version 1.0"
    next_version: str = "version 2.0"

    project_version_tickets = [
        {"version": current_version, "reference": "tds-001", "description": "tds-001"},
        {"version": current_version, "reference": "tds-002", "description": "tds-002"},
        {"version": next_version, "reference": "tds-003", "description": "tds-003"},
    ]

    project_test_ticket_scenarios = [
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
    scenarios_status = [
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
    context: Context = Context()

    def test_setup(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        set_project(
            TestDeleteScenario.project_name,
            application,
            logged,
        )
        set_project_versions(
            TestDeleteScenario.project_name,
            [
                TestDeleteScenario.current_version,
                TestDeleteScenario.next_version,
            ],
            application,
            logged,
        )
        set_project_tickets(
            TestDeleteScenario.project_name,
            TestDeleteScenario.project_version_tickets,
            application,
            logged,
        )
        set_project_repository(
            TestDeleteScenario.project_name,
            "tests/resources/repository_as_csv_feature_scenario_accross_files.csv",
            application,
            logged,
        )
        TestDeleteScenario.context.set_context(
            f"campaign/{TestDeleteScenario.current_version}/occurrence",
            set_project_campaign(
                TestDeleteScenario.project_name,
                TestDeleteScenario.current_version,
                TestDeleteScenario.project_test_ticket_scenarios,
                application,
                logged,
            ),
        )

        set_campaign_scenario_status(
            TestDeleteScenario.project_name,
            TestDeleteScenario.current_version,
            TestDeleteScenario.context.get_context(f"campaign/{TestDeleteScenario.current_version}/occurrence"),
            TestDeleteScenario.scenarios_status,
            application,
            logged,
        )

    def test_get_scenarios_from_feature(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/features/Test feature/scenarios",
            headers=logged,
        )
        assert response.status_code == 200, response.text

    def test_get_scenarios_from_feature_error_401(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/features/Test feature/scenarios",
        )
        assert response.status_code == 401, response.text

    project_epic_feature_not_found = [
        (project_name, "second_epic", "unknown"),
        (project_name, "unknown", "Test feature"),
        ("unknown", "second_epic", "Test feature"),
    ]

    @pytest.mark.parametrize("project_name,epic_ref,feature_ref", project_epic_feature_not_found)
    def test_get_scenarios_from_feature_error_404(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        epic_ref: str,
        feature_ref: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_get_scenario_from_feature_error_401(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/"
            f"features/Test feature/scenarios/t_test_1",
        )
        assert response.status_code == 401, response.text

    project_epic_feature_scenario_not_found = [
        (project_name, "second_epic", "unknown", "t_test_1"),
        (project_name, "unknown", "Test feature", "t_test_1"),
        ("unknown", "second_epic", "Test feature", "t_test_1"),
        (project_name, "second_epic", "Test feature", "unknown"),
    ]

    @pytest.mark.parametrize("project_name,epic_ref,feature_ref,scenario_ref", project_epic_feature_scenario_not_found)
    def test_get_scenario_from_feature_error_404(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        epic_ref: str,
        feature_ref: str,
        scenario_ref: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios/{scenario_ref}",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_get_scenario_from_feature(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/"
            f"features/Test feature/scenarios/t_test_1",
            headers=logged,
        )
        assert response.status_code == 200, response.text

        TestDeleteScenario.context.set_context(
            "repository/to_delete_scenario_tech_id", response.json()["scenario_tech_id"]
        )

    def test_get_scenario_from_feature_with_tech_id(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/"
            f"features/Test feature"
            f"/scenarios/{TestDeleteScenario.context.get_context('repository/to_delete_scenario_tech_id')}",
            headers=logged,
            params={"technicalId": True},
        )
        assert response.status_code == 200, response.text
        assert response.json()["scenario_id"] == "t_test_1", response.text

    def test_get_scenario_from_feature_with_tech_id_error_404(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/"
            f"features/Test feature"
            f"/scenarios/10000",
            headers=logged,
            params={"technicalId": True},
        )
        assert response.status_code == 404, response.text

    @pytest.mark.parametrize("project_name,epic_ref,feature_ref,scenario_ref", project_epic_feature_scenario_not_found)
    def test_delete_scenario_error_404(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
        epic_ref: str,
        feature_ref: str,
        scenario_ref: str,
    ) -> None:
        response = application.delete(
            f"/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios/{scenario_ref}",
            headers=logged,
        )

        assert response.status_code == 404, response.text

    def test_delete_scenario_error_401(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.delete(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/second_epic/"
            f"features/Test feature/scenarios/t_test_1",
        )

        assert response.status_code == 401, response.text

    def test_delete_scenario(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.delete(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/first_epic/"
            f"features/Test feature/scenarios/test_2",
            headers=logged,
        )

        assert response.status_code == 204, response.text

    def test_deleted_scenario_cannot_be_requested(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Deleted scenario cannot be requested repository, feature' scenarios
        response = application.get(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/epics/first_epic/"
            f"features/Test feature/scenarios/test_2",
            headers=logged,
        )
        assert response.status_code == 404, response.text

    def test_deleted_scenario_cannot_be_in_new_campaign(
        self: "TestDeleteScenario",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Deleted scenario cannot be added to new campaign
        # Create new occurrence
        response = application.post(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/campaigns",
            json={"version": TestDeleteScenario.current_version},
            headers=logged,
        )
        _occurrence: int = response.json()["occurrence"]

        response = application.put(
            f"/api/v1/projects/{TestDeleteScenario.project_name}/campaigns/{TestDeleteScenario.current_version}/{_occurrence}",
            json=TestDeleteScenario.project_test_ticket_scenarios[1],
            headers=logged,
        )
        assert response.status_code == 200, response.text
        assert dpath.get(response.json(), "raw_data/not_found_scenario") == ["test_2"], response.text


    def test_deleted_scenario_appear_on_existing_campaign(
            self: "TestDeleteScenario",
            application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        _occurrence = TestDeleteScenario.context.get_context(
            f'campaign/{TestDeleteScenario.current_version}/occurrence'
        )
        response = application.get(f"/api/v1/projects/{TestDeleteScenario.project_name}/campaigns/"
                                   f"{TestDeleteScenario.current_version}/{_occurrence}",
                                   headers=logged,
                                   )
        assert response.status_code == 200, response.text
        assert dpath.search(
            response.json(),
            "tickets/*/scenarios/*/name",
            afilter=lambda x: str(x) == 'test_2',
        ) is not None, response.text
        # Deleted scenario appear on existing campaign

    # def test_front_delete_scenario(
    #     self: "TestDeleteScenario",
    #     application: Generator[TestClient, Any, None],
    #     logged: Generator[dict[str, str], Any, None],
    # ) -> None:
    #     # Ensure setup has run and scenario_tech_id for "t_test_1" is in context
    #     # This relies on test_get_scenario_from_feature having run and populated the context
    #     scenario_tech_id_to_delete = TestDeleteScenario.context.get_context(
    #         "repository/to_delete_scenario_tech_id"
    #     )
    #     assert scenario_tech_id_to_delete is not None, "scenario_tech_id was not found in context"
    #
    #     # Scenario details for "t_test_1"
    #     project_name = TestDeleteScenario.project_name
    #     epic_name = "second_epic"
    #     feature_name = "Test feature" # As per CSV and existing tests
    #     scenario_id = "t_test_1"
    #     scenario_name_to_check = "Duplicate" # Name of t_test_1
    #
    #     # Make DELETE request to the front-end delete endpoint
    #     delete_response = application.delete(
    #         f"/front/v1/projects/{project_name}/repository/scenarios/{scenario_tech_id_to_delete}/delete",
    #         headers=logged,
    #     )
    #     assert delete_response.status_code == 200, delete_response.text
    #     # Verify the scenario name is NOT in the returned HTML table
    #     assert scenario_name_to_check not in delete_response.text, \
    #         f"Deleted scenario '{scenario_name_to_check}' found in immediate HTML response."
    #
    #     # Verify by fetching the scenarios table again via the front-end
    #     get_scenarios_response = application.get(
    #         f"/front/v1/projects/{project_name}/repository/scenarios?limit=10&skip=0", # Adjust params if needed
    #         headers=logged,
    #     )
    #     assert get_scenarios_response.status_code == 200, get_scenarios_response.text
    #     assert scenario_name_to_check not in get_scenarios_response.text, \
    #         f"Deleted scenario '{scenario_name_to_check}' found in subsequent GET request to scenarios table."
    #
    #     # Verify by trying to get the specific scenario via API (should be 404)
    #     # This uses the scenario_id 't_test_1', not the scenario_tech_id
    #     get_deleted_api_response = application.get(
    #         f"/api/v1/projects/{project_name}/epics/{epic_name}/features/{feature_name}/scenarios/{scenario_id}",
    #         headers=logged,
    #     )
    #     assert get_deleted_api_response.status_code == 404, \
    #         f"Scenario '{scenario_id}' was not properly soft-deleted; API returned {get_deleted_api_response.status_code} instead of 404."
