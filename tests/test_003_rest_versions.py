# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import re
from typing import Any, Generator
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.conftest import error_message_extraction
from tests.utils.project_setting import set_project, set_project_tickets, set_project_versions


# noinspection PyUnresolvedReferences
class TestRestVersions:
    project_name = "test_rest_versions"
    project_version = "1.0.1"
    project_new_version = "1.0.2"

    @pytest.fixture(scope="class", autouse=True)
    def _setup(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        set_project(
            TestRestVersions.project_name,
            application,
            logged,
        )
        set_project_versions(
            TestRestVersions.project_name,
            [
                TestRestVersions.project_version,
                TestRestVersions.project_new_version,
            ],
            application,
            logged,
        )

    def test_add_ticket(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
            json={"reference": "ref-001", "description": "Description"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == {"acknowledged": True, "inserted_id": 1, "message": None}

    def test_add_ticket_errors_401(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
            json={"reference": "ref-002", "description": "Description"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    ticket_error_404 = [
        ("toto", project_version, "'toto' is not registered"),
        (project_name, "2.0.0", "Version '2.0.0' is not found"),
    ]

    @pytest.mark.parametrize("project,version,message", ticket_error_404)
    def test_add_ticket_errors_404(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project: str,
        version: str,
        message: str,
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{project}/versions/{version}/tickets",
            json={"reference": "ref-002", "description": "Description"},
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_add_ticket_errors_422(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
            json={"test": "test"},
            headers=logged,
        )
        assert response.status_code == 422
        assert error_message_extraction(response.json()["detail"]) == [
            {"loc": ["body", "reference"], "msg": "Field required", "type": "missing"},
            {"loc": ["body", "description"], "msg": "Field required", "type": "missing"},
        ]

    def test_add_ticket_errors_409(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
            json={"reference": "ref-001", "description": "Description"},
            headers=logged,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]

        pattern = re.compile(
            r'duplicate key value violates unique constraint\s+"unique_ticket_project"\s+'
            r"DETAIL:\s+Key \(project_id,\s*reference\)=\(\d+,\s*ref-001\)\s+already exists\.",
            re.DOTALL,
        )

        assert pattern.search(detail), f"Unexpected detail: {detail}"
        # assert response.json()["detail"] == (
        #     "duplicate key value violates unique constraint "
        #     '"unique_ticket_project"\n'
        #     "DETAIL:  Key (project_id, reference)=(1,"
        #     " ref-001) already exists."
        # )

    def test_add_ticket_errors_500(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.tickets.add_ticket") as rp:
            rp.side_effect = Exception("error")
            response = application.post(
                f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
                json={"reference": "ref-002", "description": "Description"},
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_get_ticket(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
            headers=logged,
        )

        assert response.status_code == 200
        keys = ("status", "reference", "description", "created", "updated", "campaign_occurrences")
        assert all(key in response.json()[0].keys() for key in keys)

    @pytest.mark.parametrize("project,version,message", ticket_error_404)
    def test_get_ticket_errors_404(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project: str,
        version: str,
        message: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project}/versions/{version}/tickets",
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_ticket_errors_500(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.tickets.get_tickets") as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_get_one_ticket(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            headers=logged,
        )
        assert response.status_code == 200
        keys = ("created", "updated", "description", "reference", "status")
        assert all(key in response.json().keys() for key in keys)
        assert response.json()["reference"] == "ref-001"
        assert response.json()["description"] == "Description"
        assert response.json()["status"] == "open"

    one_ticket_error_404 = [
        (
            "toto",
            project_version,
            "ref-001",
            "'toto' is not registered",
        ),
        (
            project_name,
            "2.0.0",
            "ref-001",
            "Version '2.0.0' is not found",
        ),
        (
            project_name,
            project_version,
            "ref-002",
            f"Ticket 'ref-002' does not exist in project '{project_name}' version '{project_version}'",
        ),
    ]

    @pytest.mark.parametrize("project,version,ticket,message", one_ticket_error_404)
    def test_get_one_ticket_errors_404(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project: str,
        version: str,
        ticket: str,
        message: str,
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{project}/versions/{version}/tickets/{ticket}",
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_one_ticket_errors_500(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.tickets.get_ticket") as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_update_ticket(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            json={"description": "Updated description", "status": "in_progress"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == "1"
        response = application.get(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"
        assert response.json()["status"] == "in_progress"

        # Set the status to the actual value raise no error
        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            json={"status": "in_progress"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == "1"

    def test_update_ticket_errors_401(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            json={"description": "Updated description", "status": "in_progress"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.parametrize("project,version,ticket,message", one_ticket_error_404)
    def test_update_ticket_errors_404(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project: str,
        version: str,
        ticket: str,
        message: str,
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{project}/versions/{version}/tickets/{ticket}",
            json={"description": "Updated description", "status": "cancelled"},
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_update_ticket_move_version(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets",
            json={"reference": "mv-001", "description": "Test move"},
            headers=logged,
        )
        assert response.status_code == 200

        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/mv-001",
            json={"version": "1.0.2"},
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == "3"

    def test_update_ticket_errors_404_payload(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Set
        set_project_tickets(
            TestRestVersions.project_name,
            [
                {
                    "reference": "ref-001",
                    "version": TestRestVersions.project_version,
                    "description": "ref-001 description",
                }
            ],
            application,
            logged,
        )
        # Act
        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            json={"version": "2.0.0"},
            headers=logged,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "The version 2.0.0 is not found."

    def test_update_ticket_errors_422(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            json={"descripion": "Updated description", "status": "cancelled"},
            headers=logged,
        )
        assert response.status_code == 422
        assert error_message_extraction(response.json()["detail"]) == [
            {"loc": ["body", "descripion"], "msg": "Extra inputs are not permitted", "type": "extra_forbidden"}
        ]

        response = application.put(
            f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
            json={},
            headers=logged,
        )
        assert response.status_code == 422
        assert error_message_extraction(response.json()["detail"]) == [
            {
                "loc": ["body"],
                "msg": "Value error, UpdatedTicket must have at least one key of"
                " '('description', 'status', 'version')'",
                "type": "value_error",
            }
        ]

    def test_update_ticket_errors_500(
        self: "TestRestVersions",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.tickets.update_ticket") as rp:
            rp.side_effect = Exception("error")
            response = application.put(
                f"/api/v1/projects/{TestRestVersions.project_name}/versions/1.0.1/tickets/ref-001",
                json={"status": "cancelled"},
                headers=logged,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"
