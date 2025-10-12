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
    @pytest.mark.test_steps("Given 'test' user doesn't exist",
                       "When 'test' logs in",
                       "Then 'test' user get a 401 error")
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
        "Given 'admin' user doe exist",
        "When 'admin' logs in",
        "Then 'admin' user get a 200 response"
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
        "Then 'admin' user get a 401 error"
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
        "Then 'admin' request is returning 204"
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
        assert response.json() == [] # Weak assertion - doesn't work if played elsewhere from the start

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

    def test_create_projects(
        self: "TestSettings",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": "test"},
            headers=logged,
        )
        assert response.status_code == 200
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged,
        )
        assert response.status_code == 200
        assert response.json() == ["test"]

    fail_projects = [
        "te/st",
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
