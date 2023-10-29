# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest


class TestRestUsers:
    project_name = "test_users"
    second_project_name = "test_users2"
    current_version = "1.0.0"
    previous_version = "0.9.0"
    next_version = "1.1.0"

    def test_setup(self, application, logged):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        response = application.post("/api/v1/settings/projects",
                                    json={"name": TestRestUsers.project_name},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post("/api/v1/settings/projects",
                                    json={"name": TestRestUsers.second_project_name},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestUsers.project_name}/versions",
                                    json={"version": TestRestUsers.current_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestUsers.project_name}/versions",
                                    json={"version": TestRestUsers.previous_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestUsers.project_name}/versions",
                                    json={"version": TestRestUsers.next_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestUsers.second_project_name}/versions",
                                    json={"version": TestRestUsers.current_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestUsers.second_project_name}/versions",
                                    json={"version": TestRestUsers.previous_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestUsers.second_project_name}/versions",
                                    json={"version": TestRestUsers.next_version},
                                    headers=logged)
        assert response.status_code == 200

    # Test with only one user: the default user
    def test_get_users_error_401(self, application):
        response = application.get("/api/v1/users")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_users_error_500(self, application, logged):
        with patch('app.routers.rest.users.get_users') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/users", headers=logged)
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_get_users(self, application, logged):
        response = application.get("/api/v1/users", headers=logged)
        assert response.status_code == 200
        assert response.json() == [{"username": "admin@admin.fr",
                                    "scopes": {"*": "admin"}}]
        assert response.headers["X-total-count"] == '1'

    def test_get_users_list_1(self, application, logged):
        response = application.get("api/v1/users", headers=logged, params={"is_list": True})
        assert response.status_code == 200
        assert response.json() == ["admin@admin.fr"]

    def test_create_user_error_401(self, application):
        response = application.post("/api/v1/users",
                                    json={"username": "user1@domain.fr",
                                          "password": "pwd",
                                          "scopes": {"*": "user"}})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    payload_error_422 = [({"password": "pass"}, ['body', 'username'], 'Field required', 'missing'),
                         ({"username": "test@test.fr",
                           "alias": "test",
                           "password": "pass"}, ['body', 'alias'], 'Extra inputs are not permitted', 'extra_forbidden')]

    @pytest.mark.parametrize("payload,loc,message,err_type", payload_error_422)
    def test_create_user_error_422(self, application, logged, payload, loc, message, err_type):
        response = application.post("/api/v1/users",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 422
        assert response.json()["detail"][0]['msg'] == message
        assert response.json()["detail"][0]['loc'] == loc
        assert response.json()["detail"][0]['type'] == err_type

    def test_create_user_error_404(self, application, logged):
        response = application.post("/api/v1/users",
                                    json={"username": "test@test.fr",
                                          "password": "pwd",
                                          "scopes": {"*": "user",
                                                     "unknown": "admin"}},
                                    headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == "The projects 'unknown' are not registered."

    def test_create_user_error_400(self, application, logged):
        response = application.post("/api/v1/users",
                                    json={"username": "test@test.fr",
                                          "scopes": {"*": "user"}},
                                    headers=logged)
        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot create user without password"

    def test_create_user(self, application, logged):
        response = application.post("/api/v1/users",
                                    json={"username": "test@test.fr",
                                          "password": "test",
                                          "scopes": {"*": "user"}},
                                    headers=logged)
        assert response.status_code == 200
        assert response.json()["inserted_id"] == "2"

    def test_newly_created_user_can_log_in(self, application):
        response = application.post("/api/v1/token",
                                    data={"username": "test@test.fr",
                                          "password": "test"})
        assert response.status_code == 200
        assert response.json()["access_token"]

    def test_update_user_error_401(self, application):
        response = application.patch("/api/v1/users",
                                    json={"username": "test@test.fr"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_update_user_error_422(self, application, logged):
        response = application.patch("/api/v1/users",
                                    json={"username": "test@test.fr"},
                                    headers=logged)
        assert response.status_code == 422
        assert response.json()["detail"][0]['loc'] == ['body']
        assert response.json()["detail"][0]['msg'] == ("Value error, UpdateUser must have at least one"
                                                       " key of '('password', 'scopes')'")
        assert response.json()["detail"][0]['type'] == 'value_error'

    def test_get_user_error_401(self, application):
        response = application.get("/api/v1/users/test@test.fr")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_user_error_404(self, application, logged):
        response = application.get("/api/v1/users/unknown",
                                   headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == "User 'unknown' is not found."

    def test_get_user(self, application, logged):
        response = application.get("/api/v1/users/test@test.fr",
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == {"username": "test@test.fr", "scopes": {"*": "user"}}

    def test_update_user(self, application, logged):
        user = application.get("/api/v1/users/test@test.fr", headers=logged).json()
        response = application.patch("/api/v1/users",
                                    json={"username": "test@test.fr",
                                          "scopes": {**user["scopes"],
                                                     TestRestUsers.project_name: "user"}},
                                    headers=logged)
        assert response.status_code == 200
        response = application.get("/api/v1/users/test@test.fr",
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == {"username": "test@test.fr", "scopes": {"*": "user", TestRestUsers.project_name: "user"}}

    def test_user_scopes_200(self, application):
        # Token
        response = application.post("/api/v1/token",
                                    data={"username": "test@test.fr",
                                          "password": "test"})
        token = response.json()["access_token"]

        # Create bug on test_users -> success
        response = application.post(f"/api/v1/projects/{TestRestUsers.project_name}/bugs",
                                    json={"title": "Test user scope",
                                          "version": TestRestUsers.current_version,
                                          "description": "First description"},
                                    headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 201
        assert response.json()["inserted_id"] is not None and int(response.json()["inserted_id"])

    def test_user_scopes_403(self, application):
        # Token
        response = application.post("/api/v1/token",
                                    data={"username": "test@test.fr",
                                          "password": "test"})
        token = response.json()["access_token"]

        # Create bug on test_users2 -> not authorized
        response = application.post(f"/api/v1/projects/{TestRestUsers.second_project_name}/bugs",
                                    json={"title": "Test user scope",
                                          "version": TestRestUsers.current_version,
                                          "description": "First description"},
                                    headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        assert response.json()["detail"] == "You are not authorized to access this resource."

    def test_user_scopes_401(self, application):
        # Token
        response = application.post("/api/v1/token",
                                    data={"username": "test@test.fr",
                                          "password": "test"})
        token = response.json()["access_token"]

        # Where token expired get not authenticated
        response = application.delete("/api/v1/token",
                                      headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        response = application.post(f"/api/v1/projects/{TestRestUsers.project_name}/bugs",
                                    json={"title": "Test user scope second",
                                          "version": TestRestUsers.current_version,
                                          "description": "First description"},
                                    headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"
