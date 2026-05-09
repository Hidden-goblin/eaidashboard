# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator, List
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from app.app_exception import InvalidDeletion
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.project_schema import RegisterVersionResponse
from app.schema.users import User


# noinspection PyUnresolvedReferences


# ==================== GET /users ====================


@pytest.mark.description("Retrieve all users without authentication")
@pytest.mark.tags("users", "get", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user requests all users",
    "Then user gets 401 Unauthorized",
)
def test_get_users_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.get("/api/v1/users")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.description("Retrieve all users with server error")
@pytest.mark.tags("users", "get", "error", "500")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given server error occurs",
    "When admin requests all users",
    "Then admin gets 500 Internal Server Error",
)
def test_get_users_error_500(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 500 when business logic fails."""
    with patch("app.routers.rest.users.get_users") as mock_get_users:
        mock_get_users.side_effect = Exception("Database error")

        response = application.get("/api/v1/users", headers=logged_setting)

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


@pytest.mark.description("Retrieve all users successfully")
@pytest.mark.tags("users", "get", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "When admin requests all users",
    "Then admin gets 200 OK with user list",
)
def test_get_users_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful retrieval of all users."""
    mock_users = [
        {"username": "admin@admin.fr", "scopes": {"*": "admin"}},
        {"username": "user@example.com", "scopes": {"*": "user"}},
    ]

    with patch("app.routers.rest.users.get_users") as mock_get_users:
        mock_get_users.return_value = (mock_users, 2)

        response = application.get("/api/v1/users", headers=logged_setting)

        assert response.status_code == 200
        assert response.json() == mock_users
        assert response.headers["X-total-count"] == "2"
        mock_get_users.assert_called_once_with(
            limit=10, skip=0, project_name="*", included=True
        )


@pytest.mark.description("Retrieve all usernames successfully")
@pytest.mark.tags("users", "get", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "When admin requests all usernames",
    "Then admin gets 200 OK with username list",
)
def test_get_users_list_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful retrieval of all usernames."""
    mock_usernames = ["admin@admin.fr", "user@example.com"]

    with patch("app.routers.rest.users.get_users") as mock_get_users:
        mock_get_users.return_value = mock_usernames

        response = application.get("/api/v1/users?is_list=true", headers=logged_setting)

        assert response.status_code == 200
        assert response.json() == mock_usernames
        mock_get_users.assert_called_once_with(
            is_list=True, project_name="*", included=True
        )


@pytest.mark.description("Retrieve users with custom parameters")
@pytest.mark.tags("users", "get", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "When admin requests users with custom parameters",
    "Then admin gets 200 OK with filtered user list",
)
def test_get_users_with_parameters(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful retrieval of users with optional parameters."""
    mock_users = [{"username": "user@example.com", "scopes": {"project1": "user"}}]

    with patch("app.routers.rest.users.get_users") as mock_get_users:
        mock_get_users.return_value = (mock_users, 1)

        response = application.get(
            "/api/v1/users?limit=5&skip=1&project=project1&included=false",
            headers=logged_setting,
        )

        assert response.status_code == 200
        assert response.json() == mock_users
        assert response.headers["X-total-count"] == "1"
        mock_get_users.assert_called_once_with(
            limit=5, skip=1, project_name="project1", included=False
        )


# ==================== GET /users/{username} ====================


@pytest.mark.description("Retrieve one user without authentication")
@pytest.mark.tags("users", "get", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user requests one user",
    "Then user gets 401 Unauthorized",
)
def test_get_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.get("/api/v1/users/test@example.com")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.description("Retrieve unknown user")
@pytest.mark.tags("users", "get", "error", "404")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given user does not exist",
    "When admin requests the user",
    "Then admin gets 404 Not Found",
)
def test_get_user_error_404(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 404 when user does not exist."""
    with patch("app.routers.rest.users.get_user") as mock_get_user:
        mock_get_user.return_value = ApplicationError(error=ApplicationErrorCode.user_not_found,
                                                      message="User not found",)

        response = application.get("/api/v1/users/unknown@example.com", headers=logged_setting,)

        assert response.status_code == 404


@pytest.mark.description("Retrieve one user successfully")
@pytest.mark.tags("users", "get", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given user exists",
    "When admin requests the user",
    "Then admin gets 200 OK with user data",
)
def test_get_user_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful retrieval of one user."""
    mock_user = {"username": "test@example.com", "scopes": {"*": "user"}}

    with patch("app.routers.rest.users.get_user") as mock_get_user:
        mock_get_user.return_value = mock_user

        response = application.get("/api/v1/users/test@example.com", headers=logged_setting)

        assert response.status_code == 200
        assert response.json() == mock_user
        mock_get_user.assert_called_once_with("test@example.com")


# ==================== POST /users ====================


@pytest.mark.description("Create user without authentication")
@pytest.mark.tags("users", "create", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user creates a user",
    "Then user gets 401 Unauthorized",
)
def test_create_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.post(
        "/api/v1/users",
        json={"username": "new@example.com", "password": "password", "scopes": {"*": "user"}},
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
                "Given admin is authenticated",
                "Given payload is missing username",
                "When admin creates user",
                "Then admin gets 422 Unprocessable Entity",
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
                "Given admin is authenticated",
                "Given payload has extra field",
                "When admin creates user",
                "Then admin gets 422 Unprocessable Entity",
            )
        ],
    ),
]


@pytest.mark.description("Create user with invalid payload")
@pytest.mark.tags("users", "create", "error", "422")
@pytest.mark.parametrize("payload,loc,message,err_type", payload_error_422)
def test_create_user_error_422(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
    payload: dict,
    loc: List,
    message: str,
    err_type: str,
) -> None:
    """Test endpoint returns 422 for invalid payload."""
    response = application.post("/api/v1/users", json=payload, headers=logged_setting)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == message
    assert response.json()["detail"][0]["loc"] == loc
    assert response.json()["detail"][0]["type"] == err_type


@pytest.mark.description("Create user without password")
@pytest.mark.tags("users", "create", "error", "400")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given payload has no password",
    "When admin creates user",
    "Then admin gets 400 Bad Request",
)
def test_create_user_error_400_no_password(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 400 when password is missing."""
    response = application.post(
        "/api/v1/users",
        json={"username": "test@example.com", "scopes": {"*": "user"}},
        headers=logged_setting,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create user without password"


@pytest.mark.description("Create user with unknown project in scopes")
@pytest.mark.tags("users", "create", "error", "404")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given project does not exist",
    "When admin creates user with scope for unknown project",
    "Then admin gets 404 Not Found",
)
def test_create_user_error_404_unknown_project(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 404 when project in scopes does not exist."""
    with patch("app.routers.rest.users.create_user") as mock_create_user:
        mock_create_user.return_value = ApplicationError(error=ApplicationErrorCode.project_not_registered,
                                                         message="The projects 'unknown' are not registered.")

        response = application.post(
            "/api/v1/users",
            json={"username": "test@example.com", "password": "pass", "scopes": {"unknown": "admin"}},
            headers=logged_setting,
        )

        assert response.status_code == 404
        assert "The projects 'unknown' are not registered." in response.json()["detail"]


@pytest.mark.description("Create duplicate user")
@pytest.mark.tags("users", "create", "error", "409")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given user already exists",
    "When admin creates duplicate user",
    "Then admin gets 409 Conflict",
)
def test_create_user_error_409_duplicate(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 409 when user already exists."""
    with patch("app.routers.rest.users.create_user") as mock_create_user:
        mock_create_user.return_value = ApplicationError(error=ApplicationErrorCode.duplicate_element,
                                                         message="User already exists")

        response = application.post(
            "/api/v1/users",
            json={"username": "existing@example.com", "password": "pass", "scopes": {"*": "user"}},
            headers=logged_setting,
        )

        assert response.status_code == 409


@pytest.mark.description("Create user successfully")
@pytest.mark.tags("users", "create", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "When admin creates a new user",
    "Then admin gets 200 OK with inserted id",
)
def test_create_user_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful user creation."""
    with patch("app.routers.rest.users.create_user") as mock_create_user:
        mock_create_user.return_value = {"inserted_id": "2"}

        response = application.post(
            "/api/v1/users",
            json={"username": "new@example.com", "password": "password", "scopes": {"*": "user"}},
            headers=logged_setting,
        )

        assert response.status_code == 200
        assert response.json()["inserted_id"] == "2"
        mock_create_user.assert_called_once()


# ==================== PATCH /users ====================


@pytest.mark.description("Update user without authentication")
@pytest.mark.tags("users", "update", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user updates a user",
    "Then user gets 401 Unauthorized",
)
def test_update_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.patch("/api/v1/users", json={"username": "test@example.com"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.description("Update user without password or scopes")
@pytest.mark.tags("users", "update", "error", "422")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given payload has neither password nor scopes",
    "When admin updates user",
    "Then admin gets 422 Unprocessable Entity",
)
def test_update_user_error_422_no_fields(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 422 when neither password nor scopes are provided."""
    response = application.patch(
        "/api/v1/users", json={"username": "test@example.com"}, headers=logged_setting
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]
    assert "UpdateUser must have at least one key of" in response.json()["detail"][0]["msg"]


@pytest.mark.description("Update user with unknown project in scopes")
@pytest.mark.tags("users", "update", "error", "404")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given project does not exist",
    "When admin updates user with scope for unknown project",
    "Then admin gets 404 Not Found",
)
def test_update_user_error_404_unknown_project(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 404 when project in scopes does not exist."""
    with patch("app.routers.rest.users.update_user") as mock_update_user:
        mock_update_user.return_value = ApplicationError(error=ApplicationErrorCode.project_not_registered,
                                                         message="The projects 'unknown' are not registered.")

        response = application.patch(
            "/api/v1/users",
            json={"username": "test@example.com", "scopes": {"unknown": "admin"}},
            headers=logged_setting,
        )

        assert response.status_code == 404
        assert "The projects 'unknown' are not registered." in response.json()["detail"]


@pytest.mark.description("Update user successfully")
@pytest.mark.tags("users", "update", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "When admin updates a user",
    "Then admin gets 200 OK",
)
def test_update_user_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful user update."""
    with patch("app.routers.rest.users.update_user") as mock_update_user:
        mock_update_user.return_value = RegisterVersionResponse(inserted_id=2, message="User updated",)

        response = application.patch(
            "/api/v1/users",
            json={"username": "test@example.com", "scopes": {"*": "admin"}},
            headers=logged_setting,
        )

        assert response.status_code == 200
        mock_update_user.assert_called_once()


# ==================== PUT /users/me ====================


@pytest.mark.description("Self-update user without authentication")
@pytest.mark.tags("users", "update", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user self-updates",
    "Then user gets 401 Unauthorized",
)
def test_update_me_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.put("/api/v1/users/me", json={"password": "old", "new_password": "new"})
    assert response.status_code == 401


@pytest.mark.description("Self-update user with wrong password")
@pytest.mark.tags("users", "update", "error", "401")
@pytest.mark.test_steps(
    "Given user is authenticated",
    "Given current password is wrong",
    "When user self-updates",
    "Then user gets 401 Unauthorized",
)
def test_update_me_error_401_wrong_password(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 401 when current password is incorrect."""
    with patch("app.routers.rest.users.authenticate_user") as mock_auth:
        mock_auth.return_value = None

        response = application.put(
            "/api/v1/users/me",
            json={"password": "wrong", "new_password": "new"},
            headers=logged_setting,
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Unrecognized credentials"


@pytest.mark.description("Self-update user successfully")
@pytest.mark.tags("users", "update", "mandatory")
@pytest.mark.test_steps(
    "Given user is authenticated",
    "Given current password is correct",
    "When user self-updates",
    "Then user gets 200 OK",
)
def test_update_me_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful self-update."""
    mock_user = {"username": "user@example.com", "scopes": {"*": "user"}}

    with patch("app.routers.rest.users.authenticate_user") as mock_auth, \
         patch("app.routers.rest.users.self_update_user") as mock_update:
        mock_auth.return_value = User(**mock_user)
        mock_update.return_value = RegisterVersionResponse(inserted_id=2, message="Password updated")

        response = application.put(
            "/api/v1/users/me",
            json={"password": "current", "new_password": "new"},
            headers=logged_setting,
        )

        assert response.status_code == 200
        mock_auth.assert_called_once()
        mock_update.assert_called_once()


# ==================== DELETE /users/{username} ====================


@pytest.mark.description("Delete user without authentication")
@pytest.mark.tags("users", "delete", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user deletes a user",
    "Then user gets 401 Unauthorized",
)
def test_delete_user_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.delete("/api/v1/users/test@example.com")
    assert response.status_code == 401


@pytest.mark.description("Delete unknown user")
@pytest.mark.tags("users", "delete", "error", "400")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given user does not exist",
    "When admin deletes the user",
    "Then admin gets 400 Bad Request",
)
def test_delete_user_error_400_unknown(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 400 when user does not exist."""
    with patch("app.routers.rest.users.db_delete_user") as mock_delete:
        mock_delete.side_effect = InvalidDeletion("Invalid user")

        response = application.delete("/api/v1/users/unknown@example.com", headers=logged_setting)

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid user"


@pytest.mark.description("Delete last super admin")
@pytest.mark.tags("users", "delete", "error", "400")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given user is the last super admin",
    "When admin deletes the user",
    "Then admin gets 400 Bad Request",
)
def test_delete_user_error_400_last_admin(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 400 when trying to delete the last super admin."""
    with patch("app.routers.rest.users.db_delete_user") as mock_delete:
        mock_delete.side_effect = InvalidDeletion("Does not match the user management rules")

        response = application.delete("/api/v1/users/admin@admin.fr", headers=logged_setting)

        assert response.status_code == 400
        assert response.json()["detail"] == "Does not match the user management rules"


@pytest.mark.description("Delete user successfully")
@pytest.mark.tags("users", "delete", "mandatory")
@pytest.mark.test_steps(
    "Given admin is authenticated",
    "Given user exists",
    "When admin deletes the user",
    "Then admin gets 204 No Content",
)
def test_delete_user_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful user deletion."""
    with patch("app.routers.rest.users.db_delete_user") as mock_delete:
        mock_delete.return_value = None

        response = application.delete("/api/v1/users/test@example.com", headers=logged_setting)

        assert response.status_code == 204
        mock_delete.assert_called_once_with("test@example.com")
