# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

class TestSetting:
    def test_get_projects(self, application):

        response = application.get("/api/v1/projects")

        # Assert that the response is as expected
        assert response.status_code == 200
        assert response.json() == []

    def test_log_in(self,application):

        response = application.post("/api/v1/token")
        # Assert failing
        assert response.status_code == 422
        response = application.post("/api/v1/token", data={"username": "test", "password": "test"})
        assert response.status_code == 401

        # Assert success
        response = application.post("/api/v1/token", data={"username": "admin@admin.fr",
                                                           "password": "admin"})
        assert response.status_code == 200

    def test_log_out(self, application):
        response = application.post("/api/v1/token", data={"username": "admin@admin.fr",
                                                           "password": "admin"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token

        # Assert failing
        response = application.delete("/api/v1/token", headers={"Authorization": "Bearer"})
        assert response.status_code == 401

        # Assert success
        response = application.delete("/api/v1/token", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_create_projects(self, application, logged):
        response = application.post("/api/v1/settings/projects", json={"name": "test"}, headers=logged)
        assert response.status_code == 200