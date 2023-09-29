# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest


class TestRestProjects:
    def test_get_projects(self, application, logged):
        response = application.get("/api/v1/projects",
                                   headers=logged)
        assert response.status_code == 200
        projects = [pjt['name'] for pjt in response.json()]
        assert all(name in ["test", "test_users", "test_users2"] for name in projects)

    def test_get_projects_limit(self, application, logged):
        response = application.get("/api/v1/projects", params={"skip": 4, "limit": 2}, headers=logged)
        assert response.status_code == 200
        assert response.json() == []

    limit_outbound = [
        (-4, -2, "OFFSET must not be negative"),
        (4, -2, "LIMIT must not be negative")]

    @pytest.mark.parametrize("skip,limit,message", limit_outbound)
    def test_get_projects_limit_outbound(self, application, skip, limit, message, logged):
        response = application.get("/api/v1/projects", params={"skip": skip, "limit": limit}, headers=logged)
        assert response.status_code == 500
        assert response.json() == {"detail": message}

    def test_get_projects_errors_500(self, application, logged):
        with patch('app.routers.rest.projects.get_projects') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects", headers=logged)
            assert response.status_code == 500

    def test_get_one_project(self, application, logged):
        response = application.get("/api/v1/projects/test", headers=logged)
        assert response.status_code == 200
        assert response.json() == {'archived': [], 'current': [], 'future': [], 'name': 'test'}

    def test_get_one_projects_errors_404(self, application, logged):
        response = application.get("/api/v1/projects/unknown", headers=logged)
        assert response.status_code == 404
        assert response.json() == {"detail": "'unknown' is not registered"}

    def test_get_one_projects_errors_500(self, application, logged):
        with patch('app.routers.rest.projects.get_project') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects/test", headers=logged)
            assert response.status_code == 500
            assert response.json() == {"detail": "error"}

    def test_create_version_errors_401(self, application):
        response = application.post("/api/v1/projects/test/versions",
                                    json={"version": "1.0.0"})
        assert response.status_code == 401

    def test_create_version(self, application, logged):
        response = application.post("/api/v1/projects/test/versions",
                                    json={"version": "1.0.0"},
                                    headers=logged)
        assert response.status_code == 200
        assert response.json()["inserted_id"] == 7

    def test_create_version_errors_404(self, application, logged):
        response = application.post("/api/v1/projects/tests/versions",
                                    json={"version": "1.0.0"},
                                    headers=logged)
        assert response.status_code == 404
        assert response.json() == {"detail": "'tests' is not registered"}

    def test_create_version_errors_400(self, application, logged):
        response = application.post("/api/v1/projects/test/versions",
                                    json={"version": "1.0.0"},
                                    headers=logged)
        assert response.status_code == 400
        assert response.json() == {"detail": 'duplicate key value violates unique constraint'
                                             ' "unique_project_version"\nDETAIL:'
                                             '  Key (project_id, version)=(1, 1.0.0) already'
                                             ' exists.'}

    def test_create_version_errors_422(self, application, logged):
        response = application.post("/api/v1/projects/test/versions",
                                    json={"test": "1.0.0"},
                                    headers=logged)
        assert response.status_code == 422
        assert response.json()["detail"][0]['msg'] == 'Field required'
        assert response.json()["detail"][0]['type'] == 'missing'
        assert response.json()["detail"][0]['loc'] == ['body', 'version']

    def test_create_version_errors_500(self, application, logged):
        with patch('app.routers.rest.version.create_project_version') as rp:
            rp.side_effect = Exception("error")
            response = application.post("/api/v1/projects/test/versions",
                                        json={"version": "1.0.0"},
                                        headers=logged)
            assert response.status_code == 500
            assert response.json() == {"detail": "error"}

    def test_update_version_errors_401(self, application, logged):
        response = application.put("/api/v1/projects/test/versions/1.0.0",
                                   json={"status": "cancelled"},
                                   headers=logged)
        assert response.status_code == 200
        keys = ("version",
                "created",
                "updated",
                "started",
                "end_forecast",
                "status",
                "statistics",
                "bugs")

        assert all(key in response.json().keys() for key in keys)
        assert response.json()["status"] == "cancelled"
        # preparing other status
        response = application.post("/api/v1/projects/test/versions",
                                    json={"version": "1.0.1"},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post("/api/v1/projects/test/versions",
                                    json={"version": "1.0.2"},
                                    headers=logged)
        assert response.status_code == 200
        response = application.put("/api/v1/projects/test/versions/1.0.0",
                                   json={"status": "archived"},
                                   headers=logged)
        assert response.status_code == 200
        response = application.put("/api/v1/projects/test/versions/1.0.1",
                                   json={"status": "test plan writing"},
                                   headers=logged)
        assert response.status_code == 200

    def test_get_one_project_with_version(self, application, logged):
        response = application.get("/api/v1/projects/test", headers=logged)
        assert response.status_code == 200
        assert len(response.json()["archived"]) == 1
        assert len(response.json()["current"]) == 1
        assert len(response.json()["future"]) == 1
        assert response.json()["archived"][0]["version"] == "1.0.0"
        assert response.json()["current"][0]["version"] == "1.0.1"
        assert response.json()["future"][0]["version"] == "1.0.2"

    transition = ["test plan writing",
                  "test plan sent",
                  "test plan accepted",
                  "campaign started",
                  "campaign ended",
                  "ter writing",
                  "ter sent",
                  "archived"]

    @pytest.mark.parametrize("status", transition)
    def test_update_versions_transition(self, application, logged, status):
        response = application.put("/api/v1/projects/test/versions/1.0.2",
                                   json={"status": status},
                                   headers=logged)
        assert response.status_code == 200
        assert response.json()["status"] == status

    def test_update_versions_empty_payload(self, application, logged):
        response = application.put("/api/v1/projects/test/versions/1.0.2",
                                   json={},
                                   headers=logged)
        assert response.status_code == 200

    update_errors = [({"started": "2023:01:31"},
                      "time data '2023:01:31' does not match format '%Y-%m-%d'"),
                     ({"end_forecast": "31-01-2023"},
                      "time data '31-01-2023' does not match format '%Y-%m-%d'"),
                     ({"status": "unknown"}, "Status 'unknown' is not accepted")]

    @pytest.mark.parametrize("payload,message", update_errors)
    def test_update_versions_400(self, application, logged, payload, message):
        response = application.put("/api/v1/projects/test/versions/1.0.2",
                                   json=payload,
                                   headers=logged)
        assert response.status_code == 400
        assert response.json()["detail"] == message

    def test_update_versions_500(self, application, logged):
        with patch('app.routers.rest.version.update_version_data') as rp:
            rp.side_effect = Exception("error")
            response = application.put("/api/v1/projects/test/versions/1.0.1",
                                       json={"status": "cancelled"},
                                       headers=logged)
            assert response.status_code == 500
            assert response.json() == {"detail": "error"}

    def test_get_version(self, application, logged):
        response = application.get("/api/v1/projects/test/versions/1.0.1",
                                   headers=logged)
        assert response.status_code == 200
        keys = ("bugs",
                "statistics",
                "status",
                "version",
                "created",
                "updated")
        assert all(key in response.json().keys() for key in keys)
        assert response.json()["version"] == "1.0.1"
        assert response.json()["status"] == "test plan writing"

    version_errors_404 = [("toto", "1.0.1", "'toto' is not registered"),
                          ("test", "2.0.0", "Version '2.0.0' is not found")]

    @pytest.mark.parametrize("project,version,message", version_errors_404)
    def test_get_version_errors_404(self, application,logged, project, version, message):
        response = application.get(f"/api/v1/projects/{project}/versions/{version}",
                                   headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_version_errors_500(self, application, logged):
        with patch('app.routers.rest.version.get_version') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects/test/versions/1.0.1",
                                       headers=logged)
            assert response.status_code == 500
            assert response.json() == {"detail": "error"}
