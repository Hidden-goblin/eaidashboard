# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from random import choice
from typing import Any, Generator

import dpath
from starlette.testclient import TestClient

from tests.utils.api_model import (
    log_in,
    log_out,
)
from tests.utils.context_manager import Context
from tests.utils.project_setting import (
    set_project,
    set_project_campaign,
    set_project_repository,
    set_project_tickets,
    set_project_users,
    set_project_versions,
)


# noinspection PyUnresolvedReferences
class TestRestCampaignWorkflow:
    """
    Test a complete test campaign workflow.

    Initial status is:
    - Project and version exist
    - Test repository exists
    - Campaign occurrence is set

    The process is:
    1. Snapshot the initial status (all tests are in TODO)
        This is the first test:
            - log in as admin
            - check the campaign
            - snapshot the status
            - log out
    2. Create the test evidence, execute test and record bug
        This is the second test:
            - log in as user
            - retrieve the test evidence for one ticket
            - Update the status of one test to "waiting fix"
            - Create a new bug with link to the failing test
            - log out
    3. Retrieve bugs check link exists
        This is the third test:
            - log in as admin
            - retrieve bugs
            - check failing scenario appears in the bug
            - log out
    4. Snapshot the current state
        This is the fourth test:
            - log in as user
            - update the remaining scenario status
            - create the snapshot of the current campaign status
            - log out
    5. Retrieve the campaign state
        This is the fifth test:
            - log in as admin
            - retrieve campaign testing status
            - update the campaign status
            - generate the campaign report
            - log out
    """

    project_name = "test_campaign_workflow"
    project_version = {"past": "0.9", "current": "1.0", "next": "1.1"}
    project_version_list = [
        "0.9",
        "1.0",
        "1.1",
    ]
    dev_tickets = {
        "first": {"reference": "ref-001", "description": "Description of first"},
        "second": {"reference": "ref-002", "description": "Description of second"},
        "third": {"reference": "ref-003", "description": "Description of third"},
    }
    dev_tickets_list = [
        {
            "version": "1.0",
            "reference": "ref-001",
            "description": "Description of first",
        },
        {
            "version": "1.0",
            "reference": "ref-002",
            "description": "Description of second",
        },
        {
            "version": "1.0",
            "reference": "ref-003",
            "description": "Description of third",
        },
    ]

    project_campaign = [
        {
            "ticket_reference": "ref-001",
            "scenarios": [
                {
                    "epic": "first_epic",
                    "feature_name": "Test feature",
                    "scenario_id": "test_1",
                },
                {
                    "epic": "first_epic",
                    "feature_name": "New Test feature",
                    "scenario_id": "test_1",
                },
            ],
        },
        {
            "ticket_reference": "ref-002",
            "scenarios": [
                {
                    "epic": "second_epic",
                    "feature_name": "Test feature",
                    "scenario_id": "t_test_1",
                },
            ],
        },
    ]
    usul = {
        "username": "user@testrestcampaignworkflow.com",
        "password": "user1234",
        "scopes": {
            "*": "user",
            project_name: "user",
        },
    }
    alfred = {
        "username": "admin@testrestcampaignworkflow.com",
        "password": "admin1234",
        "scopes": {
            "*": "user",
            project_name: "admin",
        },
    }

    users = [
        usul,
        alfred,
    ]

    current_campaign_occurrence = None
    context: Context = Context()

    def test_setup(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        # Create project
        set_project(
            TestRestCampaignWorkflow.project_name,
            application,
            logged,
        )
        # Create users
        set_project_users(
            TestRestCampaignWorkflow.users,
            application,
            logged,
        )
        # Create versions
        set_project_versions(
            TestRestCampaignWorkflow.project_name,
            TestRestCampaignWorkflow.project_version_list,
            application,
            logged,
        )
        # Create test repository
        set_project_repository(
            TestRestCampaignWorkflow.project_name,
            "tests/resources/repository_as_csv.csv",
            application,
            logged,
        )
        # Add development tickets
        set_project_tickets(
            TestRestCampaignWorkflow.project_name,
            TestRestCampaignWorkflow.dev_tickets_list,
            application,
            logged,
        )
        # Create campaign for current version
        TestRestCampaignWorkflow.current_campaign_occurrence = set_project_campaign(
            TestRestCampaignWorkflow.project_name,
            "1.0",
            TestRestCampaignWorkflow.project_campaign,
            application,
            logged,
        )

    def test_retrieve_campaign_and_snapshot(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
    ) -> None:
        """
        - log in as admin
        - check the campaign
        - snapshot the status
        - log out
        """
        header = log_in(
            TestRestCampaignWorkflow.alfred,
            application,
        )
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}/tickets",
            headers=header,
        )
        assert response.status_code == 200
        assert response.json()["project_name"] == TestRestCampaignWorkflow.project_name
        assert response.json()["version"] == TestRestCampaignWorkflow.project_version["current"]
        assert response.json()["occurrence"] == 1

        tickets = dpath.values(response.json(), "tickets/*/reference")
        assert all(item in tickets for item in ["ref-001", "ref-002"])

        response = application.post(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}",
            headers=header,
        )
        assert response.status_code == 200

        log_out(
            header,
            application,
        )

    # Process test, record bug, link test to bug
    def test_workflow_test_and_record_bug(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
    ) -> None:
        """- log in as user
        - retrieve the test evidence for one ticket
        - Update the status of one test to "waiting fix"
        - Create a new bug with link the failing test
        - log out"""
        header = log_in(
            TestRestCampaignWorkflow.usul,
            application,
        )

        # Retrieve evidence template
        response = application.get(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}/deliverables",
            params={
                "project_name": TestRestCampaignWorkflow.project_name,
                "version": TestRestCampaignWorkflow.project_version["current"],
                "occurrence": TestRestCampaignWorkflow.current_campaign_occurrence,
                "deliverable_type": "evidence",
                "ticket_ref": "ref-002",
            },
            headers=header,
        )

        assert response.status_code == 200, response.text
        assert "ref-002" in response.text, response.text

        response = application.get(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}"
            f"/tickets/ref-002",
            headers=header,
        )
        assert response.status_code == 200
        # Test scenario
        scenario_internal_id: int = dpath.get(
            response.json(),
            "*/internal_id",
        )  # one scenario by design
        # Update status
        response = application.put(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}"
            f"/tickets/ref-002"
            f"/scenarios/{scenario_internal_id}/status",
            headers=header,
            params={"new_status": "waiting fix"},
        )
        assert response.status_code == 200, response.text
        TestRestCampaignWorkflow.context.set_context(
            f"scenarios_result/{scenario_internal_id}",
            "waiting fix",
        )
        TestRestCampaignWorkflow.context.set_context(
            "scenario_tech_id",
            scenario_internal_id,
        )
        # Create bug with link
        response = application.post(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}/bugs",
            headers=header,
            json={
                "version": "1.0",
                "title": "[Workflow] Linked bug to ref-002",
                "description": "Overflow",
                "criticality": "blocking",
                "related_to": [
                    {
                        "ticket_reference": "ref-002",
                        "scenario_tech_id": scenario_internal_id,
                        "occurrence": TestRestCampaignWorkflow.current_campaign_occurrence,
                    },
                ],
            },
        )

        assert response.status_code == 201, response.text
        TestRestCampaignWorkflow.context.set_context(
            "bugs",
            {
                "ticket_reference": "ref-002",
                "scenario_tech_id": scenario_internal_id,
                "bug_id": response.json()["inserted_id"],
            },
        )
        log_out(
            header,
            application,
        )

    def test_check_bugs_in_the_version(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
    ) -> None:
        """- log in as admin
        - retrieve bugs
        - check failing scenario appears in the bug
        - log out"""
        header = log_in(
            TestRestCampaignWorkflow.alfred,
            application,
        )
        response = application.get(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}/bugs",
            headers=header,
            params={
                "version": "1.0",
                "status": [
                    "open",
                ],
            },
        )
        assert response.status_code == 200, response.text
        assert any(
            elem[1] == TestRestCampaignWorkflow.context.get_context("bugs/bug_id")
            for elem in dpath.search(
                response.json(),
                "*/internal_id",
                yielded=True,
            )
        ), response.text
        response = application.get(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}/bugs/"
            f"{TestRestCampaignWorkflow.context.get_context('bugs/bug_id')}",
            headers=header,
        )
        assert response.status_code == 200, response.text
        assert {
            "ticket_reference": TestRestCampaignWorkflow.context.get_context("bugs/ticket_reference"),
            "scenario_tech_id": TestRestCampaignWorkflow.context.get_context("bugs/scenario_tech_id"),
            "occurrence": TestRestCampaignWorkflow.current_campaign_occurrence,
        } in response.json()["related_to"], response.text

        log_out(
            header,
            application,
        )

    def test_complete_the_testing_day(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
    ) -> None:
        """- log in as user
        - update the remaining scenario status
        - create the snapshot of the current campaign status
        - log out"""
        header = log_in(
            TestRestCampaignWorkflow.usul,
            application,
        )

        response = application.get(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}"
            f"/tickets/ref-001",
            headers=header,
        )
        assert response.status_code == 200

        for _, _scenario_id in dpath.search(response.json(), "*/internal_id", yielded=True):
            # Update status
            _new_status = choice(["cancelled", "done"])
            resp = application.put(
                f"api/v1/projects/{TestRestCampaignWorkflow.project_name}"
                f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
                f"/{TestRestCampaignWorkflow.current_campaign_occurrence}"
                f"/tickets/ref-001"
                f"/scenarios/{_scenario_id}/status",
                headers=header,
                params={"new_status": _new_status},
            )
            TestRestCampaignWorkflow.context.set_context(
                f"scenarios_result/{_scenario_id}",
                _new_status,
            )
            assert resp.status_code == 200, resp.text

        response = application.post(
            f"/api/v1/projects/{TestRestCampaignWorkflow.project_name}"
            f"/campaigns/{TestRestCampaignWorkflow.project_version['current']}"
            f"/{TestRestCampaignWorkflow.current_campaign_occurrence}",
            headers=header,
        )
        assert response.status_code == 200

        log_out(
            header,
            application,
        )

    def test_test_manager_report_campaign_advancement(
        self: "TestRestCampaignWorkflow",
        application: Generator[TestClient, Any, None],
    ) -> None:
        """- log in as admin
        - retrieve campaign testing status
        - update the campaign status
        - generate the campaign report
        - log out"""
        header = log_in(
            TestRestCampaignWorkflow.alfred,
            application,
        )

        response = application.get(
            f"api/v1/projects/{TestRestCampaignWorkflow.project_name}/testResults",
            headers={**header, "accept": "application/json"},
            params={
                "category": "scenarios",
                "rendering": "map",
                "version": "1.0",
                "campaign_occurrence": TestRestCampaignWorkflow.current_campaign_occurrence,
            },
        )

        def simple_cast(status: str) -> str:
            """Mimic app.database.utils.test_result_management.__convert_scenario_status_to_three_state"""
            match status:
                case "done":
                    return "passed"
                case "waiting fix":
                    return "failed"
                case _:
                    return "skipped"

        assert response.status_code == 200, response.text
        test_results = list(zip(response.json().get("element_id"), response.json().get("element_status")))
        assert all(item[1] == "skipped" for index, item in enumerate(test_results) if index <= 2), test_results
        assert test_results[3][1] == simple_cast(
            TestRestCampaignWorkflow.context.get_context(f"scenarios_result/{test_results[3][0]}")
        ), TestRestCampaignWorkflow.context.get_context(f"scenarios_result/{test_results[3][0]}")
        assert test_results[4][1] == simple_cast(
            TestRestCampaignWorkflow.context.get_context(f"scenarios_result/{test_results[4][0]}")
        ), TestRestCampaignWorkflow.context.get_context(f"scenarios_result/{test_results[4][0]}")
        assert test_results[5][1] == simple_cast(
            TestRestCampaignWorkflow.context.get_context(f"scenarios_result/{test_results[5][0]}")
        ), TestRestCampaignWorkflow.context.get_context(f"scenarios_result/{test_results[5][0]}")
