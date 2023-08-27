# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest


class TestRestVersions:
    def test_add_ticket(self, application, logged):
        response = application.post("/api/v1/projects/test/versions/1.0.1/tickets",
                                    json={"reference": "ref-001",
                                          "description": "Description"},
                                    headers=logged)
        assert response.status_code == 200
        assert response.json() == {"acknowledged": True, "inserted_id": "1", "message": None}

    def test_add_ticket_errors_401(self, application):
        response = application.post("/api/v1/projects/test/versions/1.0.1/tickets",
                                    json={"reference": "ref-002",
                                          "description": "Description"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    ticket_error_404 = [("toto", "1.0.1", "'toto' is not registered"),
                        ("test", "2.0.0", "Version '2.0.0' is not found")]

    @pytest.mark.parametrize("project,version,message", ticket_error_404)
    def test_add_ticket_errors_404(self, application, logged, project, version, message):
        response = application.post(f"/api/v1/projects/{project}/versions/{version}/tickets",
                                    json={"reference": "ref-002",
                                          "description": "Description"},
                                    headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_add_ticket_errors_422(self, application, logged):
        response = application.post("/api/v1/projects/test/versions/1.0.1/tickets",
                                    json={"test": "test"},
                                    headers=logged)
        assert response.status_code == 422
        assert response.json()["detail"] == [{'loc': ['body', 'reference'],
                                              'msg': 'field required',
                                              'type': 'value_error.missing'},
                                             {'loc': ['body', 'description'],
                                              'msg': 'field required',
                                              'type': 'value_error.missing'}
                                             ]

    def test_add_ticket_errors_400(self, application, logged):
        response = application.post("/api/v1/projects/test/versions/1.0.1/tickets",
                                    json={"reference": "ref-001",
                                          "description": "Description"},
                                    headers=logged)
        assert response.status_code == 400
        assert response.json()["detail"] == ('duplicate key value violates unique constraint '
                                             '"unique_ticket_project"\n'
                                             'DETAIL:  Key (project_id, reference)=(1,'
                                             ' ref-001) already exists.')

    def test_add_ticket_errors_500(self, application, logged):
        with patch('app.routers.rest.version.add_ticket') as rp:
            rp.side_effect = Exception("error")
            response = application.post("/api/v1/projects/test/versions/1.0.1/tickets",
                                        json={"reference": "ref-002",
                                              "description": "Description"},
                                        headers=logged)
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_get_ticket(self, application):
        response = application.get("/api/v1/projects/test/versions/1.0.1/tickets")

        assert response.status_code == 200
        keys = ("status", "reference", "description", "created", "updated", "campaign_occurrences")
        assert all(key in response.json()[0].keys() for key in keys)

    @pytest.mark.parametrize("project,version,message", ticket_error_404)
    def test_get_ticket_errors_404(self, application, project, version, message):
        response = application.get(f"/api/v1/projects/{project}/versions/{version}/tickets")
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_ticket_errors_500(self, application):
        with patch('app.routers.rest.version.get_tickets') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects/test/versions/1.0.1/tickets")
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_get_one_ticket(self, application):
        response = application.get("/api/v1/projects/test/versions/1.0.1/tickets/ref-001")
        assert response.status_code == 200
        keys = ("created",
                "updated",
                "description",
                "reference",
                "status")
        assert all(key in response.json().keys() for key in keys)
        assert response.json()["reference"] == "ref-001"
        assert response.json()["description"] == "Description"
        assert response.json()["status"] == "open"

    one_ticket_error_404 = [("toto", "1.0.1", "ref-001", "'toto' is not registered"),
                            ("test", "2.0.0", "ref-001", "Version '2.0.0' is not found"),
                            ("test",
                             "1.0.1",
                             "ref-002",
                             "Ticket 'ref-002' does not exist"
                             " in project 'test' version '1.0.1'")]

    @pytest.mark.parametrize("project,version,ticket,message", one_ticket_error_404)
    def test_get_one_ticket_errors_404(self, application, project, version, ticket, message):
        response = application.get(
            f"/api/v1/projects/{project}/versions/{version}/tickets/{ticket}")
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_one_ticket_errors_500(self, application):
        with patch('app.routers.rest.version.get_ticket') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects/test/versions/1.0.1/tickets/ref-001")
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_update_ticket(self, application, logged):
        response = application.put("/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
                                   json={"description": "Updated description",
                                         "status": "in_progress"},
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == "1"
        response = application.get("/api/v1/projects/test/versions/1.0.1/tickets/ref-001")
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"
        assert response.json()["status"] == "in_progress"

        # Set the status to the actual value raise no error
        response = application.put("/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
                                   json={"status": "in_progress"},
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == "1"

    def test_update_ticket_errors_401(self, application):
        response = application.put("/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
                                   json={"description": "Updated description",
                                         "status": "in_progress"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.parametrize("project,version,ticket,message", one_ticket_error_404)
    def test_update_ticket_errors_404(self, application, logged, project, version, ticket, message):
        response = application.put(
            f"/api/v1/projects/{project}/versions/{version}/tickets/{ticket}",
            json={"description": "Updated description",
                  "status": "cancelled"},
            headers=logged
        )
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_update_ticket_move_version(self, application, logged):
        response = application.post("/api/v1/projects/test/versions/1.0.1/tickets",
                                    json={"reference": "mv-001",
                                          "description": "Test move"},
                                    headers=logged)
        assert response.status_code == 200

        response = application.put(
            "/api/v1/projects/test/versions/1.0.1/tickets/mv-001",
            json={"version": "1.0.2"},
            headers=logged
        )
        assert response.status_code == 200
        assert response.json() == "3"

    def test_update_ticket_errors_404_payload(self, application, logged):
        response = application.put(
            "/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
            json={"version": "2.0.0"},
            headers=logged
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "The version 2.0.0 is not found."

    def test_update_ticket_errors_422(self, application, logged):
        response = application.put(
            "/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
            json={"descripion": "Updated description",
                  "status": "cancelled"},
            headers=logged
        )
        assert response.status_code == 422
        assert response.json()["detail"] == [{'loc': ['body', 'descripion'],
                                              'msg': 'extra fields not permitted',
                                              'type': 'value_error.extra'}
                                             ]

        response = application.put(
            "/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
            json={},
            headers=logged
        )
        assert response.status_code == 422
        assert response.json()["detail"] == [{'loc': ['body', '__root__'],
                                              'msg': "UpdatedTicket must have at least one key of"
                                                     " '('description', 'status', 'version')'",
                                              'type': 'value_error'}]

    def test_update_ticket_errors_500(self, application, logged):
        with patch('app.routers.rest.version.update_ticket') as rp:
            rp.side_effect = Exception("error")
            response = application.put(
                "/api/v1/projects/test/versions/1.0.1/tickets/ref-001",
                json={"status": "cancelled"},
                headers=logged
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "error"
