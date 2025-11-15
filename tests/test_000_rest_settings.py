# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator
from unittest.mock import patch

import jwt
import pytest
from starlette.testclient import TestClient


# noinspection PyUnresolvedReferences
class TestSettings:
    @pytest.mark.path("/authentication")
    @pytest.mark.tags("authentication", "error", "422", "401")
    @pytest.mark.test_steps(
        "Given 'test' user doesn't exist", "When 'test' logs in", "Then 'test' user get a 401 error"
    )
    @pytest.mark.description("Check log bad request and unauthorized")
    def test_log_in_errors(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.post("/api/v1/token")
        # Assert failing
        assert response.status_code == 422
        response = application.post(
            "/api/v1/token",
            data={"username": "test", "password": "test"},
        )
        assert response.status_code == 401

    @pytest.mark.path("/authentication")
    @pytest.mark.tags("authentication", "mandatory")
    @pytest.mark.test_steps(
        "Given 'admin' user doe exist", "When 'admin' logs in", "Then 'admin' user get a 200 response"
    )
    @pytest.mark.description("Unupdated admin can log in")
    def test_log_in_success(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
    ) -> None:
        # Assert success
        response = application.post(
            "/api/v1/token",
            data={"username": "admin@admin.fr", "password": "admin"},
        )
        assert response.status_code == 200

    @pytest.mark.path("/authentication")
    @pytest.mark.tags("authentication", "error", "401")
    @pytest.mark.test_steps(
        "Given 'admin' user does exist",
        "Given 'admin' user is logged in",
        "Given 'admin' user doesn't provide its token",
        "When 'admin' logs off",
        "Then 'admin' user get a 401 error",
    )
    @pytest.mark.description("Cannot log off without token")
    def test_log_out_error(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
    ) -> None:
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

    @pytest.mark.path("/authentication")
    @pytest.mark.tags("authentication", "mandatory")
    @pytest.mark.test_steps(
        "Given 'admin' user does exist",
        "Given 'admin' user is logged in",
        "When 'admin' logs off",
        "Then 'admin' request is returning 204",
    )
    @pytest.mark.description("Check success logg out request")
    def test_log_out_success(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
    ) -> None:
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
            headers={"Authorization": f"Bearer {token}"},
        )
        # Assert
        assert response.status_code == 204, response.text

    @pytest.mark.path("/projects/management")
    @pytest.mark.test_steps(
        "Given 'admin' is logged in",
        "When 'admin' requests the project list",
        "Then 'admin' retrieve a list")
    @pytest.mark.tags("projects", "mandatory")
    @pytest.mark.description("Simple setting route validation, no content validation")
    def test_registered_projects_200(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        # Action
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged,
        )

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.path("/projects/management")
    @pytest.mark.tags("projects", "authorization", "error", "401")
    @pytest.mark.test_steps(
        "Given 'admin' provides a token without username",
        "When 'admin' requests the project list",
        "Then 'admin' get '401' status code"
    )
    def test_authorization_error_no_email(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.database.authorization.token_user") as rp:
            rp.return_value = None
            response = application.get(
                "/api/v1/settings/projects",
                headers=logged,
            )
            assert response.status_code == 401, response.text

    @pytest.mark.path("/projects/management")
    @pytest.mark.tags("projects", "authorization", "error", "401")
    @pytest.mark.test_steps(
        "Given 'admin' provides a token",
        "Given 'admin' user doesn't exist",
        "When 'admin' requests the project list",
        "Then 'admin' gets '401' status code"
    )
    #TODO: review this case as it doesn't make sense for admin
    def test_authorization_error_user_not_found(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.database.authorization.get_user") as rp:
            rp.return_value = None
            response = application.get(
                "/api/v1/settings/projects",
                headers=logged,
            )
            assert response.status_code == 401, response.text

    @pytest.mark.path("/projects/management")
    @pytest.mark.test_steps(
        "Given 'admin' is logged in",
        "Given 'admin' waits for too long",
        "when 'admin' requests the project list",
        "Then 'admin' gets '401' status code" )
    @pytest.mark.tags("error", "401", "projects", "authorization")
    def test_authorization_error_signature_error(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.database.authorization.token_user") as rp:
            rp.side_effect = jwt.InvalidSignatureError("Error")
            response = application.get(
                "/api/v1/settings/projects",
                headers=logged,
            )
            assert response.status_code == 401, response.text

    @pytest.mark.path("/projects/management")
    @pytest.mark.test_steps(
        "Given 'admin' is logged in",
        "Given an unhandled error occurs",
        "When 'admin' requests the project list",
        "Then 'admin' gets '500' status code"
    )
    @pytest.mark.tags("projects", "error", "500")
    def test_registered_projects_errors_500(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.settings.settings.registered_projects") as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                "/api/v1/settings/projects",
                headers=logged,
            )
            assert response.status_code == 500

    @pytest.mark.path("/projects/management")
    @pytest.mark.tags("projects", "create", "mandatory")
    @pytest.mark.test_steps(
        "Given 'admin' is logged in",
        "Given 'test' project does not exits",
        "When 'admin' creates 'test' projects",
        "Then 'admin' gets 'test' in the project list"
    )
    @pytest.mark.description("Register a new empty project. We add randomness seed to avoid test collision")
    def test_create_projects(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        import random
        project_name: str = f"test-{random.randrange(1000)}"

        response = application.get(
            "/api/v1/settings/projects",
            headers=logged,
        )
        if project_name in response.json():
            pytest.skip(t"{project_name} to be created already exists in database")

        response = application.post(
            "/api/v1/settings/projects",
            json={"name": project_name},
            headers=logged,
        )
        assert response.status_code == 200
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged,
        )
        assert response.status_code == 200
        assert project_name in response.json(), response.text

    fail_projects = [
        pytest.param("te/st",marks=pytest.mark.test_steps("one")),
        "te\\st",
        "te$st",
        "longlonglonglonglonglonglonglonglonglonglonglonglonglonglonglong",
        "*",
    ]

    @pytest.mark.parametrize("project_name", fail_projects)
    def test_create_projects_errors_400(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
        project_name: str,
    ) -> None:
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": project_name},
            headers=logged,
        )
        assert response.status_code == 400

    def test_create_projects_errors_401(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": "test"},
        )
        assert response.status_code == 401

    def test_create_projects_errors_409(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": "test"},
            headers=logged,
        )
        assert response.status_code == 409

    def test_create_projects_errors_500(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with patch("app.routers.rest.settings.settings.register_project") as rp:
            rp.side_effect = Exception("error")
            response = application.post(
                "/api/v1/settings/projects",
                json={"name": "test"},
                headers=logged,
            )
            assert response.status_code == 500
