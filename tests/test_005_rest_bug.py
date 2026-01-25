# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator, List
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.status_enum import BugStatusEnum
from tests.conftest import error_message_extraction

# noinspection PyUnresolvedReferences

PROJECT_NAME = "test_bug"
CURRENT_VERSION = "1.0.0"
PREVIOUS_VERSION = "0.9.0"
NEXT_VERSION = "1.1.0"
SPECIFIC_BUG = {
    "title": "SPECIFIC",
    "version": CURRENT_VERSION,
    "description": "First, only mandatory field",
    "status": "open",
    "criticality": "major",
    "url": "",
}


@pytest.fixture
def specific_bug(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> int:
    """

    Args:
        application:
        logged_setting:

    Returns:

    """
    # Create if not exist
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        headers=logged_setting,
    )

    specific_internal_id = None
    for item in response.json():
        if item["title"] == "SPECIFIC" and item["version"] == CURRENT_VERSION:
            specific_internal_id = item["internal_id"]
            break
    if specific_internal_id is None:
        response = application.post(
            f"/api/v1/projects/{PROJECT_NAME}/bugs",
            json=SPECIFIC_BUG,
            headers=logged_setting,
        )
        specific_internal_id = response.json()["inserted_id"]
    else:
        response = application.put(
            f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_internal_id}",
            json=SPECIFIC_BUG,
            headers=logged_setting,
        )
        assert response.status_code < 300
    yield specific_internal_id


@pytest.fixture(scope="module", autouse=True)
def _setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    """setup any state specific to the execution of the given class (which
    usually contains tests).
    """
    response = application.post(
        "/api/v1/settings/projects",
        json={"name": PROJECT_NAME},
        headers=logged_setting,
    )
    assert response.status_code == 200
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions",
        json={"version": CURRENT_VERSION},
        headers=logged_setting,
    )
    assert response.status_code == 200
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions",
        json={"version": PREVIOUS_VERSION},
        headers=logged_setting,
    )
    assert response.status_code == 200
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/versions",
        json={"version": NEXT_VERSION},
        headers=logged_setting,
    )
    assert response.status_code == 200
    application.cookies.set("access_token", "")
    yield


def test_get_bugs_from_project(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_bugs_from_project_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        "/api/v1/projects/unknown/bugs",
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "'unknown' is not registered"


def test_get_bugs_from_project_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.bugs.db_g_bugs") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/bugs",
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"


def test_create_bug_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json={
            "version": f"{CURRENT_VERSION}",
            "title": "first bug",
            "description": "lorem ipsum dolor",
            "url": "",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


create_error_404 = [
    (
        "unknown",
        {"title": "First bug", "version": CURRENT_VERSION, "description": "Desc"},
        "'unknown' is not registered",
    ),
    (
        PROJECT_NAME,
        {"title": "First bug", "version": "5.0.0", "description": "Desc"},
        "Version '5.0.0' is not found",
    ),
    ("unknown", {"title": "First bug", "version": "5.0.0", "description": "Desc"}, "'unknown' is not registered"),
]


@pytest.mark.parametrize("project_name,payload,message", create_error_404)
def test_create_bug_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    project_name: str,
    payload: dict,
    message: str,
) -> None:
    response = application.post(
        f"/api/v1/projects/{project_name}/bugs",
        json=payload,
        headers=logged_setting,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == message


payload_error_422 = [
    (
        {},
        [
            {"loc": ["body", "version"], "msg": "Field required", "type": "missing"},
            {"loc": ["body", "title"], "msg": "Field required", "type": "missing"},
            {"loc": ["body", "description"], "msg": "Field required", "type": "missing"},
        ],
    ),
    (
        {"version": "1.0.0"},
        [
            {"loc": ["body", "title"], "msg": "Field required", "type": "missing"},
            {"loc": ["body", "description"], "msg": "Field required", "type": "missing"},
        ],
    ),
    (
        {
            "version": f"{CURRENT_VERSION}",
            "title": "First bug",
            "description": "Not to be created",
            "comment": "mine",
        },
        [{"loc": ["body", "comment"], "msg": "Extra inputs are not permitted", "type": "extra_forbidden"}],
    ),
]


@pytest.mark.parametrize("payload,message", payload_error_422)
def test_create_bug_error_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    payload: dict,
    message: List[dict],
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json=payload,
        headers=logged_setting,
    )
    assert response.status_code == 422
    assert all(msg in message for msg in error_message_extraction(response.json()["detail"]))


def test_create_bug_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.bugs.insert_bug") as rp:
        rp.side_effect = Exception("error")
        response = application.post(
            f"/api/v1/projects/{PROJECT_NAME}/bugs",
            json={
                "title": "First",
                "version": CURRENT_VERSION,
                "description": "First, only mandatory field",
            },
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"


# Could be flaky because of id
create_payload = [
    ({"title": "First", "version": CURRENT_VERSION, "description": "First, only mandatory field"}, 2),
    (
        {
            "title": "Second",
            "version": CURRENT_VERSION,
            "criticality": "minor",
            "description": "Second, with criticality set",
        },
        3,
    ),
    (
        {
            "title": "Third",
            "version": CURRENT_VERSION,
            "url": "no check on url",
            "description": "Third, with url set",
        },
        4,
    ),
]


@pytest.mark.parametrize("payload,inserted_id", create_payload)
def test_create_bug(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    payload: dict,
    inserted_id: int,
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json=payload,
        headers=logged_setting,
    )
    assert response.status_code == 201
    assert isinstance(response.json()["inserted_id"], int)


duplicate_error = [
    (
        {"title": "Third", "version": CURRENT_VERSION, "description": "Third (duplicate),only mandatory"},
        (f"Cannot insert existing bug for '{PROJECT_NAME}', '{CURRENT_VERSION}', 'Third'.\nPlease check your data."),
    ),
    # ({"title": "third",
    #   "version": current_version,
    #   "description": "Third (duplicate),only mandatory"},
    #  (
    #      f"Cannot insert existing bug for '{project_name}', "
    #      f"'{current_version}', 'third'.\nPlease check your data.")
    #  )
]


@pytest.mark.parametrize("payload,message", duplicate_error)
def test_create_bug_error_409(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    payload: dict,
    message: str,
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json=payload,
        headers=logged_setting,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == message


populate_bug = [
    {"title": "First-past", "version": PREVIOUS_VERSION, "description": "First, only mandatory field"},
    {
        "title": "Second-past",
        "version": PREVIOUS_VERSION,
        "criticality": "minor",
        "description": "Second, with criticality set",
    },
    {
        "title": "Third-past",
        "version": PREVIOUS_VERSION,
        "criticality": "blocking",
        "description": "Third, with criticality set",
    },
    {"title": "First-past", "version": NEXT_VERSION, "description": "First, only mandatory field"},
    {
        "title": "Second-past",
        "version": NEXT_VERSION,
        "criticality": "minor",
        "description": "Second, with criticality set",
    },
    {
        "title": "Third-past",
        "version": NEXT_VERSION,
        "criticality": "blocking",
        "description": "Third, with criticality set",
    },
]


@pytest.mark.parametrize("payload", populate_bug)
def test_create_bug_populate(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    payload: dict,
) -> None:
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json=payload,
        headers=logged_setting,
    )
    assert response.status_code == 201


def test_get_bugs_from_project_multi_version(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) == 9


def test_get_bugs_from_specific_version(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        params={"version": PREVIOUS_VERSION},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


bugs_project_filter = [
    ({"status": [BugStatusEnum.fix_ready.value, BugStatusEnum.closed.value]}, 0),
    ({"criticality": BugCriticalityEnum.major.value}, 4),
]


@pytest.mark.parametrize("payload,count", bugs_project_filter)
def test_get_bugs_from_version_filter(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    payload: dict,
    count: int,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        params=payload,
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert len(response.json()) == count


def test_get_bug(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        headers=logged_setting,
    )
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "SPECIFIC"
    assert response.json()["version"] == CURRENT_VERSION
    assert response.json()["description"] == "First, only mandatory field"
    assert response.json()["url"] == ""
    assert response.json()["criticality"] == "major"
    assert response.json()["status"] == "open"
    assert response.json()["created"] == response.json()["updated"]


def test_get_bug_internal_id_not_found(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/100",
        headers=logged_setting,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Bug '100' is not found."


def test_get_bug_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get(
        "/api/v1/projects/unknown/bugs/1",
        headers=logged_setting,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "'unknown' is not registered"


def test_get_bug_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.bugs.db_get_bug") as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            f"/api/v1/projects/{PROJECT_NAME}/bugs/1",
            headers=logged_setting,
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "error"


def test_update_bug_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/1",
        json={"title": "First updated"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


update_bug_404 = [
    ("unknown", "1", {"title": "First updated"}, "'unknown' is not registered"),
    (PROJECT_NAME, "100", {"title": "First updated"}, "Bug '100' is not found."),
    (PROJECT_NAME, "2", {"version": "6.6.6"}, "The version '6.6.6' is not found."),
]


@pytest.mark.parametrize("project_name,bug_id,payload,message", update_bug_404)
def test_update_bug_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    project_name: str,
    bug_id: str,
    payload: dict,
    message: str,
) -> None:
    response = application.put(
        f"/api/v1/projects/{project_name}/bugs/{bug_id}",
        json=payload,
        headers=logged_setting,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == message


def test_update_bug_error_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/1",
        json={"status": "reopen"},
        headers=logged_setting,
    )

    assert response.status_code == 422
    assert error_message_extraction(response.json()["detail"]) == [
        {
            "loc": ["body", "status"],
            "msg": "Input should be 'open', 'closed', 'closed not a defect' or 'fix ready'",
            "type": "enum",
        }
    ]


def test_update_bug_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.bugs.db_update_bugs") as rp:
        rp.side_effect = Exception("error")
        response = application.put(
            f"/api/v1/projects/{PROJECT_NAME}/bugs/1",
            json={"title": "First updated"},
            headers=logged_setting,
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "error"


def test_update_bug(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        json={"title": "First updated"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json()["criticality"] == "major"
    assert response.json()["description"] == "First, only mandatory field"
    assert response.json()["status"] == "open"
    assert response.json()["title"] == "First updated"
    assert response.json()["url"] == ""
    assert response.json()["version"] == "1.0.0"


def test_update_bug_status(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        json={"status": "fix ready"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "fix ready"


def test_update_bug_status_error(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        json={"status": "fixe ready"},
        headers=logged_setting,
    )
    assert response.status_code == 422


def test_update_bug_status_transition(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.get(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "open"
    assert response.json()["criticality"] == "major"
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        json={"status": "open", "criticality": "blocking"},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "open"
    assert response.json()["criticality"] == "blocking"


def test_update_bug_version_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        json={"version": "2.0.0"},
        headers=logged_setting,
    )
    assert response.status_code == 404


def test_update_bug_version(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    specific_bug: int,
) -> None:
    response = application.put(
        f"/api/v1/projects/{PROJECT_NAME}/bugs/{specific_bug}",
        json={"version": PREVIOUS_VERSION},
        headers=logged_setting,
    )
    assert response.status_code == 200
