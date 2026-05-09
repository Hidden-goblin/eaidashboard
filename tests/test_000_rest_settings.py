# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Callable, Generator
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from starlette.testclient import TestClient

from app.app_exception import DuplicateProject
from app.database.authorization import oauth2_scheme
from app.schema.project_schema import Project
from app.schema.users import User

# noinspection PyUnresolvedReferences


@pytest.mark.path("/authentication")
@pytest.mark.tags("authentication", "error", "422", "401", "api")
@pytest.mark.test_steps(
    "Given 'test' user doesn't exist",
    "When 'test' logs in",
    "Then 'test' user get a 401 error",
)
@pytest.mark.description("Check log bad request and unauthorized")
def test_log_in_errors(
    application: Generator[TestClient, Any, None],
) -> None:
    with patch("app.routers.rest.auth.authenticate_user") as mock_authenticate_user:
        mock_authenticate_user.return_value = None
        response = application.post("/api/v1/token")
        # Assert failing
        assert response.status_code == 422
        response = application.post(
            "/api/v1/token",
            data={"username": "test", "password": "test"},
        )
        assert response.status_code == 401


@pytest.mark.path("/authentication")
@pytest.mark.tags("authentication", "mandatory", "api")
@pytest.mark.test_steps(
    "Given 'admin' user doe exist",
    "When 'admin' logs in",
    "Then 'admin' user get a 200 response",
)
@pytest.mark.description("Unupdated admin can log in")
def test_log_in_success(
    application: Generator[TestClient, Any, None],
) -> None:
    with (
        patch("app.routers.rest.auth.authenticate_user") as mock_authenticate_user,
        patch("app.database.authentication.register_connection") as mock_create_access_token,
    ):
        mock_authenticate_user.return_value = User(username="admin@admin.fr", scopes={"*": "admin"})
        mock_create_access_token.return_value = 0
        # Assert success
        response = application.post(
            "/api/v1/token",
            data={"username": "admin@admin.fr", "password": "admin"},
        )
        assert response.status_code == 200, response.text


@pytest.mark.path("/authentication")
@pytest.mark.tags("authentication", "error", "401", "api")
@pytest.mark.test_steps(
    "Given 'admin' user does exist",
    "Given 'admin' user is logged in",
    "Given 'admin' user doesn't provide its token",
    "When 'admin' logs off",
    "Then 'admin' user get a 401 error",
)
@pytest.mark.description("Cannot log off without token")
def test_log_out_error(
    application: Generator[TestClient, Any, None],
) -> None:
    with (
        patch("app.routers.rest.auth.authenticate_user") as mock_authenticate_user,
        patch("app.database.authentication.register_connection") as mock_create_access_token,
    ):
        mock_authenticate_user.return_value = User(username="admin@admin.fr", scopes={"*": "admin"})
        mock_create_access_token.return_value = 0
        # Prepare
        response = application.post(
            "/api/v1/token",
            data={"username": "admin@admin.fr", "password": "admin"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token

        # Action
        response = application.delete(
            "/api/v1/token",
            headers={"Authorization": "Bearer"},
        )

        # Assert
        assert response.status_code == 401

@pytest.fixture
def mock_oauth2_scheme(application: TestClient) -> Generator[str, None, None]:
    token = "test-token"
    application.app.dependency_overrides[oauth2_scheme] = lambda: token
    yield token
    application.app.dependency_overrides.pop(oauth2_scheme, None)


@pytest.mark.path("/authentication")
@pytest.mark.tags("authentication", "mandatory", "api")
@pytest.mark.test_steps(
    "Given 'admin' user does exist",
    "Given 'admin' user is logged in",
    "When 'admin' logs off",
    "Then 'admin' request is returning 204",
)
@pytest.mark.description("Check success log out request")
def test_log_out_success(
    application: Generator[TestClient, Any, None],
        logged_setting : dict[str, str],
        mock_oauth2_scheme:str,
) -> None:
    with patch("app.routers.rest.auth.invalidate_token") as mock_invalidate_token:
        response = application.delete(
            "/api/v1/token",
            headers=logged_setting,
        )

        assert response.status_code == 204, response.text
        mock_invalidate_token.assert_called_once_with(mock_oauth2_scheme)


@pytest.mark.path("/projects/management")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "When 'admin' requests the project list",
    "Then 'admin' retrieve a list",
)
@pytest.mark.tags("projects", "mandatory")
@pytest.mark.description("Simple setting route validation, no content validation")
def test_registered_projects_200(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    with (
        patch("app.routers.rest.settings.settings.registered_projects") as mock_get_projects,
    ):
        # Prepare
        mock_get_projects.return_value = []
        # Action
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged_setting,
        )

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.path("/projects/management")
@pytest.mark.tags("projects", "authorization", "error", "401")
@pytest.mark.test_steps(
    "Given 'admin' is not logged in",
    "When 'admin' requests the project list",
    "Then 'admin' gets '401' status code",
)
def test_project_list_missing_authentication(
    application: Generator[TestClient, Any, None],
    mock_security: Callable[..., dict[str, str]],
) -> None:
    headers = mock_security(status_code=401)

    response = application.get(
        "/api/v1/settings/projects",
        headers=headers,
    )
    assert response.status_code == 401, response.text

@pytest.mark.path("/projects/management")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given an unhandled error occurs",
    "When 'admin' requests the project list",
    "Then 'admin' gets '500' status code",
)
@pytest.mark.tags("projects", "error", "500")
def test_registered_projects_errors_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.settings.settings.registered_projects", new_callable=AsyncMock) as rp:
        rp.side_effect = Exception("error")
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged_setting,
        )
        assert response.status_code == 500


@pytest.mark.path("/projects/management")
@pytest.mark.tags("projects", "create", "mandatory")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given 'test' project does not exits",
    "When 'admin' creates 'test' projects",
    "Then 'admin' gets 'test' in the project list",
)
@pytest.mark.description("Register a new empty project.")
def test_create_projects(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    project_name: str = "test"

    with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock, return_value=project_name) as rp:
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": project_name},
            headers=logged_setting,
        )
        assert response.status_code == 200
        assert Project(name=project_name).model_dump() == response.json(), response.text




@pytest.mark.path("/projects/management")
@pytest.mark.tags("projects", "create", "error", "409")
@pytest.mark.test_steps(
    "Given 'admin' is log in",
    "Given 'admin' provide 'test' project name",
    "Given 'test' project does exist"
    "When 'admin' creates 'test' project",
    "Then 'admin' gets '409' status code",
)
def test_create_projects_errors_409(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock) as rp:
        rp.side_effect = DuplicateProject("test exists")
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": "test"},
            headers=logged_setting,
        )
        assert response.status_code == 409


@pytest.mark.path("/projects/management")
@pytest.mark.tags("projects", "creation", "error", "401")
@pytest.mark.test_steps(
    "Given 'anonymous' is querying",
    "When 'anonymous' creates 'test' project",
    "Then 'anonymous' gets '401' status code",
)
def test_create_projects_errors_401(
    application: Generator[TestClient, Any, None],
) -> None:
    response = application.post(
        "/api/v1/settings/projects",
        json={"name": "test"},
    )
    assert response.status_code == 401


@pytest.mark.path("/projects/management")
@pytest.mark.tags("projects", "creation", "error", "500")
@pytest.mark.test_steps(
    "Given 'admin' is logged in",
    "Given an unhandled error occurs",
    "When 'admin' creates 'test' project",
    "Then 'admin' gets '500' status code",
)
def test_create_projects_errors_500(
    application: Generator[TestClient, Any, None],
    logged_setting: Generator[dict[str, str], Any, None],
) -> None:
    with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock) as rp:
        rp.side_effect = Exception("error")
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": "test"},
            headers=logged_setting,
        )
        assert response.status_code == 500
