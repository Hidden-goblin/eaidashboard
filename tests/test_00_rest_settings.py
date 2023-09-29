# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest


class TestSettings:

    def test_log_in_errors(self, application):
        response = application.post("/api/v1/token")
        # Assert failing
        assert response.status_code == 422
        response = application.post("/api/v1/token",
                                    data={"username": "test", "password": "test"})
        assert response.status_code == 401

    def test_log_in_success(self, application):
        # Assert success
        response = application.post("/api/v1/token",
                                    data={"username": "admin@admin.fr",
                                          "password": "admin"})
        assert response.status_code == 200

    def test_log_out_error(self, application):
        response = application.post("/api/v1/token",
                                    data={"username": "admin@admin.fr",
                                          "password": "admin"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token

        # Assert failing
        response = application.delete("/api/v1/token",
                                      headers={"Authorization": "Bearer"})
        assert response.status_code == 401

    def test_log_out_success(self, application):
        response = application.post("/api/v1/token",
                                    data={"username": "admin@admin.fr",
                                          "password": "admin"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token
        # Assert success
        response = application.delete("/api/v1/token",
                                      headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_registered_projects_200(self, application, logged):
        response = application.get("/api/v1/settings/projects",
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == []

    def test_registered_projects_errors_500(self, application, logged):
        with patch('app.routers.rest.settings.registered_projects') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/settings/projects",
                                       headers=logged)
            assert response.status_code == 500

    def test_create_projects(self, application, logged):
        response = application.post("/api/v1/settings/projects",
                                    json={"name": "test"},
                                    headers=logged)
        assert response.status_code == 200
        response = application.get("/api/v1/settings/projects",
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == ["test"]

    fail_projects = ["te/st",
                     "te\\st",
                     "te$st",
                     "longlonglonglonglonglonglonglonglonglonglonglonglonglonglonglong",
                     "*"]

    @pytest.mark.parametrize("project_name", fail_projects)
    def test_create_projects_errors_400(self, application, logged, project_name):
        response = application.post("/api/v1/settings/projects", json={"name": project_name},
                                    headers=logged)
        assert response.status_code == 400

    def test_create_projects_errors_401(self, application, logged):
        response = application.post("/api/v1/settings/projects", json={"name": "test"})
        assert response.status_code == 401

    def test_create_projects_errors_409(self, application, logged):
        response = application.post("/api/v1/settings/projects",
                                    json={"name": "test"},
                                    headers=logged)
        assert response.status_code == 409

    def test_create_projects_errors_500(self, application, logged):
        with patch('app.routers.rest.settings.register_project') as rp:
            rp.side_effect = Exception("error")
            response = application.post("/api/v1/settings/projects",
                                        json={"name": "test"},
                                        headers=logged)
            assert response.status_code == 500
