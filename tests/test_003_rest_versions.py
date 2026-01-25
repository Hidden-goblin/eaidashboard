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

PROJECT_NAME = "test_rest_versions"
PROJECT_VERSION = "1.0.1"
PROJECT_NEW_VERSION = "1.0.2"


@pytest.fixture(autouse=True)
def _setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    set_project(
        PROJECT_NAME,
        application,
        logged_setting,
    )
    set_project_versions(
        PROJECT_NAME,
        [
            PROJECT_VERSION,
            PROJECT_NEW_VERSION,
        ],
        application,
        logged_setting,
    )
    application.cookies.set("access_token", "")
    yield


def test_add_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
        json={"reference": "ref-001", "description": "Description"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == {"acknowledged": True, "inserted_id": 1, "message": None}


def test_add_ticket_errors_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
        json={"reference": "ref-002", "description": "Description"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


ticket_error_404 = [
    ("toto", PROJECT_VERSION, "'toto' is not registered"),
    (PROJECT_NAME, "2.0.0", "Version '2.0.0' is not found"),
]


@pytest.mark.parametrize("project,version,message", ticket_error_404)
def test_add_ticket_errors_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    project: str,
    version: str,
    message: str,
) -> None:
    response = application.post(
        f"/api/v1/projects/{project}/versions/{version}/tickets",
        json={"reference": "ref-002", "description": "Description"},
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == message


def test_add_ticket_errors_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
        json={"test": "test"},
        headers=logged_setting,
    )
    assert response.status_code == 422
    assert error_message_extraction(response.json()["detail"]) == [
        {"loc": ["body", "reference"], "msg": "Field required", "type": "missing"},
        {"loc": ["body", "description"], "msg": "Field required", "type": "missing"},
    ]


def test_add_ticket_errors_409(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
        json={"reference": "ref-001", "description": "Description"},
        headers=logged_setting,
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
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.tickets.add_ticket") as rp:
        rp.side_effect = Exception("error")
        response = application.post(
            f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
            json={"reference": "ref-002", "description": "Description"},
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"


def test_get_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
        headers=logged_setting,
    )

    assert response.status_code == 200
    keys = ("status", "reference", "description", "created", "updated", "campaign_occurrences")
    assert all(key in response.json()[0].keys() for key in keys)


@pytest.mark.parametrize("project,version,message", ticket_error_404)
def test_get_ticket_errors_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    project: str,
    version: str,
    message: str,
) -> None:
    response = application.get(
        f"/api/v1/projects/{project}/versions/{version}/tickets",
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == message


def test_get_ticket_errors_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.tickets.get_tickets") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"


def test_get_one_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        headers=logged_setting,
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
        PROJECT_VERSION,
        "ref-001",
        "'toto' is not registered",
    ),
    (
        PROJECT_NAME,
        "2.0.0",
        "ref-001",
        "Version '2.0.0' is not found",
    ),
    (
        PROJECT_NAME,
        PROJECT_VERSION,
        "ref-002",
        f"Ticket 'ref-002' does not exist in project '{PROJECT_NAME}' version '{PROJECT_VERSION}'",
    ),
]


@pytest.mark.parametrize("project,version,ticket,message", one_ticket_error_404)
def test_get_one_ticket_errors_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    project: str,
    version: str,
    ticket: str,
    message: str,
) -> None:
    response = application.get(
        f"/api/v1/projects/{project}/versions/{version}/tickets/{ticket}",
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == message


def test_get_one_ticket_errors_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.tickets.get_ticket") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"


def test_update_ticket(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        json={"description": "Updated description", "status": "in_progress"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == "1"
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"
    assert response.json()["status"] == "in_progress"

    # Set the status to the actual value raise no error
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        json={"status": "in_progress"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == "1"


def test_update_ticket_errors_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        json={"description": "Updated description", "status": "in_progress"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.parametrize("project,version,ticket,message", one_ticket_error_404)
def test_update_ticket_errors_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    project: str,
    version: str,
    ticket: str,
    message: str,
) -> None:
    response = application.put(
        f"/api/v1/projects/{project}/versions/{version}/tickets/{ticket}",
        json={"description": "Updated description", "status": "cancelled"},
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == message


def test_update_ticket_move_version(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets",
        json={"reference": "mv-001", "description": "Test move"},
        headers=logged_setting,
    )
    assert response.status_code == 200

    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/mv-001",
        json={"version": "1.0.2"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == "3"


def test_update_ticket_errors_404_payload(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    # Set
    set_project_tickets(
        PROJECT_NAME,
        [
            {
                "reference": "ref-001",
                "version": PROJECT_VERSION,
                "description": "ref-001 description",
            }
        ],
        application,
        logged_setting,
    )
    # Act
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        json={"version": "2.0.0"},
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "The version 2.0.0 is not found."


def test_update_ticket_errors_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        json={"descripion": "Updated description", "status": "cancelled"},
        headers=logged_setting,
    )
    assert response.status_code == 422
    assert error_message_extraction(response.json()["detail"]) == [
        {"loc": ["body", "descripion"], "msg": "Extra inputs are not permitted", "type": "extra_forbidden"}
    ]

    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
        json={},
        headers=logged_setting,
    )
    assert response.status_code == 422
    assert error_message_extraction(response.json()["detail"]) == [
        {
            "loc": ["body"],
            "msg": "Value error, UpdatedTicket must have at least one key of '('description', 'status', 'version')'",
            "type": "value_error",
        }
    ]


def test_update_ticket_errors_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.tickets.update_ticket") as rp:
        rp.side_effect = Exception("error")
        response = application.put(
            f"/api/v1/projects/{PROJECT_NAME}/versions/1.0.1/tickets/ref-001",
            json={"status": "cancelled"},
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"
