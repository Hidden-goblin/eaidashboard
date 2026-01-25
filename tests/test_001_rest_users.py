# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator, List
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests.conftest import status_404_error_message_check
from tests.utils.project_setting import set_project, set_project_versions

# noinspection PyUnresolvedReferences

PROJECT_NAME = "test_users"
SECOND_PROJECT_NAME = "test_users2"
CURRENT_VERSION = "1.0.0"
PREVIOUS_VERSION = "0.9.0"
NEXT_VERSION = "1.1.0"


@pytest.fixture(autouse=True)
def _setup(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    """setup any state specific to the execution of the given class (which
    usually contains tests).
    """
    for project in [PROJECT_NAME, SECOND_PROJECT_NAME]:
        set_project(project, application, logged_setting)

    _versions = [
        PREVIOUS_VERSION,
        CURRENT_VERSION,
        NEXT_VERSION,
    ]
    for project in [PROJECT_NAME, SECOND_PROJECT_NAME]:
        set_project_versions(
            project,
            _versions,
            application,
            logged_setting,
        )
    application.cookies.set("access_token", "")
    yield


# Test with only one user: the default user
@pytest.mark.path("/users/retrieve_all")
@pytest.mark.tags("users", "get", "error", "401")
@pytest.mark.description("Test retrieving all users without authentication")
@pytest.mark.test_steps(
    "Given 'anonymous' is querying",
    "When 'anonymous' retrieves all users",
    "Then 'anonymous' gets a '401' status code",
    "Then 'anonymous' gets a 'Could not validate credentials' error message",
)
def test_get_users_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.get("/api/v1/users")
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Could not validate credentials", response.text


@pytest.mark.path("/users/retrieve_all")
@pytest.mark.tags("users", "get", "error", "500")
@pytest.mark.description("Test retrieving all users with server error")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given an unhandled error occurs",
    "When 'admin' retrieves all users",
    "Then 'admin' gets a '500' status code",
    "Then 'admin' gets an 'error' error message",
)
def test_get_users_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.users.get_users") as rp:
        rp.side_effect = Exception("error")
        response = application.get("/api/v1/users", headers=logged_setting)
        assert response.status_code == 500, response.text
        assert response.json()["detail"] == "error", response.text


@pytest.mark.path("/users/retrieve_all")
@pytest.mark.tags("users", "get", "mandatory")
@pytest.mark.description("Test retrieving all users")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "When 'admin' retrieves all users",
    "Then 'admin' finds at least himself",
    "Then 'admin' validates the number of elements is '>= 1'",
)
def test_get_users(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get("/api/v1/users", headers=logged_setting)
    assert response.status_code == 200
    assert {"username": "admin@admin.fr", "scopes": {"*": "admin"}} in response.json(), response.text
    assert int(response.headers["X-total-count"]) >= 1, f"Number of elements is {response.headers['X-total-count']}"


@pytest.mark.path("/users/retrieve_all")
@pytest.mark.tags("users", "get", "mandatory")
@pytest.mark.description("Test retrieving all usernames")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "When 'admin' retrieves all usernames",
    "Then 'admin' finds at least himself",
)
def test_get_users_list_1(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get("api/v1/users", headers=logged_setting, params={"is_list": True})
    assert response.status_code == 200, response.text
    assert "admin@admin.fr" in response.json(), response.text


@pytest.mark.path("/users/create")
@pytest.mark.tags("users", "create", "error", "401")
@pytest.mark.description("Test creating a user without authentication")
@pytest.mark.test_steps(
    "Given 'anonymous' is querying",
    "When 'anonymous' creates 'user1' user",
    "Then 'anonymous' gets a '401' status code",
    "Then 'anonymous' gets a 'Could not validate credentials' error message",
)
def test_create_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.post(
        "/api/v1/users", json={"username": "user1@domain.fr", "password": "pwd", "scopes": {"*": "user"}}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


payload_error_422 = [
    pytest.param(
        {"password": "pass"},
        ["body", "username"],
        "Field required",
        "missing",
        marks=[
            pytest.mark.test_steps(
                "Given 'admin' is logged in",
                "Given 'admin' prepares a payload without 'username'",
                "When 'admin' creates '' user",
                "Then 'admin' gets a '422' status code",
                "Then 'admin' gets a 'Field required' error message for 'body/username'",
            )
        ],
    ),
    pytest.param(
        {"username": "test@test.fr", "alias": "test", "password": "pass"},
        ["body", "alias"],
        "Extra inputs are not permitted",
        "extra_forbidden",
        marks=[
            pytest.mark.test_steps(
                "Given 'admin' is logged in",
                "Given 'admin' prepares a payload with extra field 'alias'",
                "When 'admin' creates 'test' user",
                "Then 'admin' gets a '422' status code",
                "Then 'admin' gets an 'Extra inputs are not permitted' error message for 'body/alias'",
            )
        ],
    ),
]


@pytest.mark.path("/users/create")
@pytest.mark.tags("users", "create", "error", "422")
@pytest.mark.parametrize("payload,loc,message,err_type", payload_error_422)
def test_create_user_error_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
    payload: dict,
    loc: List,
    message: str,
    err_type: str,
) -> None:
    response = application.post("/api/v1/users", json=payload, headers=logged_setting)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == message
    assert response.json()["detail"][0]["loc"] == loc
    assert response.json()["detail"][0]["type"] == err_type


@pytest.mark.path("/users/create")
@pytest.mark.tags("users", "create", "error", "404")
@pytest.mark.description("Cannot create a user assigning role on unknown project")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given 'unknown' project does not exist",
    "When 'admin' creates 'test_unknown' user",
    "Then 'admin' gets a '404' status code",
    "Then 'admin' gets a 'The projects 'unknown' are not registered.' error message",
)
def test_create_user_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    # Ensure 'unknown' project does not exist
    response = application.get("/api/v1/setting/projects", headers=logged_setting, params={"is_list": True})
    assert "unknown" not in response.json(), "Precondition failed: 'unknown' project exists"

    # Action
    response = application.post(
        "/api/v1/users",
        json={"username": "test_unknown@test.fr", "password": "pwd", "scopes": {"*": "user", "unknown": "admin"}},
        headers=logged_setting,
    )
    assert response.status_code == 404, response.text
    status_404_error_message_check(response, "The projects 'unknown' are not registered.")


@pytest.mark.path("/users/create")
@pytest.mark.tags("users", "create", "error", "400")
@pytest.mark.description("Cannot create a user without password")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given 'admin' prepares a payload without password",
    "When 'admin' creates 'test_passwordless' user",
    "Then 'admin' gets a '400' status code",
    "Then 'admin' gets a 'Cannot create user without password' error message",
)
def test_create_user_error_400(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.post(
        "/api/v1/users", json={"username": "test_passwordless@test.fr", "scopes": {"*": "user"}}, headers=logged_setting
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create user without password"


@pytest.mark.path("/users/create")
@pytest.mark.tags("users", "create", "mandatory")
@pytest.mark.description("Test creating a new user")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given 'test' user does not exist",
    "When 'admin' creates 'test' user",
    "Then 'admin' gets the new user internal id",
)
def test_create_user(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    # Pre-condition: ensure 'test' user does not exist
    response = application.get("/api/v1/users", headers=logged_setting, params={"is_list": True})
    assert "test@test.fr" not in response.json(), "Precondition failed: 'test' user exists"

    # Action: create 'test' user
    response = application.post(
        "/api/v1/users",
        json={"username": "test@test.fr", "password": "test", "scopes": {"*": "user"}},
        headers=logged_setting,
    )
    assert response.status_code == 200
    assert response.json()["inserted_id"] == "2"


@pytest.mark.path("/users")
@pytest.mark.tags("users", "login", "mandatory")
@pytest.mark.description("Test logging in with newly created user")
@pytest.mark.test_steps(
    "Given 'test' user is created",
    "When 'test' user logs in",
    "Then 'test' user gets an access token",
)
def test_newly_created_user_can_log_in(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    # Pre-condition: ensure 'test' user exists
    response = application.get("/api/v1/users", params={"is_list": True}, headers=logged_setting)
    if "test@test.fr" not in response.json():
        response = application.post(
            "/api/v1/users",
            json={"username": "test@test.fr", "password": "test", "scopes": {"*": "user"}},
            headers=logged_setting,
        )
        assert response.status_code == 200, "Precondition failed: could not create 'test' user"

    # Action: log in with 'test' user
    response = application.post(
        "/api/v1/token",
        data={"username": "test@test.fr", "password": "test"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.path("/users/create")
@pytest.mark.tags("users", "create", "error", "409")
@pytest.mark.description("Cannot create a duplicate user")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given 'test@test.fr' user already exists",
    "When 'admin' creates 'test@test.fr' user",
    "Then 'admin' gets a '409' status code",
)
def test_create_user_duplicate_error(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    # Pre-condition: ensure 'test@test.fr' user exists
    response = application.get("/api/v1/users", params={"is_list": True}, headers=logged_setting)
    if "test@test.fr" not in response.json():
        response = application.post(
            "/api/v1/users",
            json={"username": "test@test.fr", "password": "test", "scopes": {"*": "user"}},
            headers=logged_setting,
        )
        assert response.status_code == 200, "Precondition failed: could not create 'test' user"

    # Action: attempt to create duplicate 'test@test.fr' user
    response = application.post(
        "/api/v1/users",
        json={"username": "test@test.fr", "password": "test", "scopes": {"*": "user"}},
        headers=logged_setting,
    )
    assert response.status_code == 409


@pytest.mark.path("/users/update")
@pytest.mark.tags("users", "update", "error", "401")
@pytest.mark.description("Cannot update a user wihhout authentication")
@pytest.mark.test_steps(
    "Given 'anonymous' is querying",
    "When 'anonymous' updates 'test@test.fr' user",
    "Then 'anonymous' gets a '401' status code",
    "Then 'anonymous' gets a 'Could not validate credentials' error message",
)
def test_update_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.patch("/api/v1/users", json={"username": "test@test.fr"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.path("/users/update")
@pytest.mark.tags("users", "update", "error", "422")
@pytest.mark.description("Cannot update a user without either password or scopes")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given 'admin' prepares a payload without 'password' and 'scopes'",
    "When 'admin' updates 'test@test.fr' user",
    "Then 'admin' gets a '422' status code",
    "Then 'admin' gets a 'Value error, UpdateUser must have at least one key of "
    "'('password', 'scopes')'' error message",
)
def test_update_user_error_422(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.patch("/api/v1/users", json={"username": "test@test.fr"}, headers=logged_setting)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]
    assert response.json()["detail"][0]["msg"] == (
        "Value error, UpdateUser must have at least one key of '('password', 'scopes')'"
    )
    assert response.json()["detail"][0]["type"] == "value_error"


def test_get_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.get("/api/v1/users/test@test.fr")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_user_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get("/api/v1/users/unknown", headers=logged_setting)
    status_404_error_message_check(response, "User 'unknown' is not found.")


def test_get_user(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    response = application.get("/api/v1/users/test@test.fr", headers=logged_setting)
    assert response.status_code == 200
    assert response.json() == {"username": "test@test.fr", "scopes": {"*": "user"}}


def test_update_user(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    user = application.get("/api/v1/users/test@test.fr", headers=logged_setting).json()
    response = application.patch(
        "/api/v1/users",
        json={"username": "test@test.fr", "scopes": {**user["scopes"], PROJECT_NAME: "user"}},
        headers=logged_setting,
    )
    assert response.status_code == 200
    response = application.get("/api/v1/users/test@test.fr", headers=logged_setting)
    assert response.status_code == 200
    assert response.json() == {
        "username": "test@test.fr",
        "scopes": {"*": "user", PROJECT_NAME: "user"},
    }


def test_user_scopes_200(
    application: Generator[TestClient, Any, None],
) -> None:
    # Token
    response = application.post("/api/v1/token", data={"username": "test@test.fr", "password": "test"})
    token = response.json()["access_token"]

    # Create bug on test_users -> success
    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json={
            "title": "Test user scope",
            "version": CURRENT_VERSION,
            "description": "First description",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["inserted_id"] is not None and int(response.json()["inserted_id"])


def test_user_scopes_403(
    application: Generator[TestClient, Any, None],
) -> None:
    # Token
    response = application.post("/api/v1/token", data={"username": "test@test.fr", "password": "test"})
    token = response.json()["access_token"]

    # Create bug on test_users2 -> not authorized
    response = application.post(
        f"/api/v1/projects/{SECOND_PROJECT_NAME}/bugs",
        json={
            "title": "Test user scope",
            "version": CURRENT_VERSION,
            "description": "First description",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "You are not authorized to access this resource."


def test_user_scopes_401(
    application: Generator[TestClient, Any, None],
) -> None:
    # Token
    response = application.post("/api/v1/token", data={"username": "test@test.fr", "password": "test"})
    token = response.json()["access_token"]

    # Where token expired get Could not validate credentials
    response = application.delete("/api/v1/token", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    response = application.post(
        f"/api/v1/projects/{PROJECT_NAME}/bugs",
        json={
            "title": "Test user scope second",
            "version": CURRENT_VERSION,
            "description": "First description",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_delete_user(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    _users = application.get("/api/v1/users", headers=logged_setting)
    if "test@test.fr" not in [item["username"] for item in _users.json()]:
        response = application.post(
            "/api/v1/users",
            json={"username": "test@test.fr", "password": "test", "scopes": {"*": "user"}},
            headers=logged_setting,
        )
        assert response.status_code == 200
    _del_user = application.delete("/api/v1/users/test@test.fr", headers=logged_setting)
    assert _del_user.status_code == 204


def test_delete_user_400_last_super_admin(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    # Set test so that only one super admin exist
    _users = application.get("/api/v1/users", headers=logged_setting)
    for user in _users.json():
        if user["username"] != "admin@admin.fr":
            application.delete(f"/api/v1/users/{user['username']}", headers=logged_setting)
    # Test removing last super admin is not possible
    _del_user = application.delete("/api/v1/users/admin@admin.fr", headers=logged_setting)
    assert _del_user.status_code == 400
    assert _del_user.json()["detail"] == "Does not match the user management rules"


def test_delete_user_400_unknown_user(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    _del_user = application.delete("/api/v1/users/fake@fake.lu", headers=logged_setting)
    assert _del_user.status_code == 400
    assert _del_user.json()["detail"] == "Invalid user"
