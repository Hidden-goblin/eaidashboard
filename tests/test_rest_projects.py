# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest


@pytest.mark.order(after="tests/test_rest_settings.py::TestSettings")
class TestRestProjects:
    def test_get_projects(self, application):
        response = application.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == [{'archived': 0, 'current': 0, 'future': 0, 'name': 'test'}]

    def test_get_projects_limit(self, application):
        response = application.get("/api/v1/projects", params={"skip": 4, "limit": 2})
        assert response.status_code == 200
        assert response.json() == []

    def test_get_projects_limit_outbound(self, application):
        response = application.get("/api/v1/projects", params={"skip": -4, "limit": -2})
        assert response.status_code == 500
        assert response.json() == {"detail": "InvalidRowCountInResultOffsetClause('OFFSET must not "
                                             "be negative')"}
        response = application.get("/api/v1/projects", params={"skip": 4, "limit": -2})
        assert response.status_code == 500
        assert response.json() == {"detail": "InvalidRowCountInLimitClause('LIMIT must not "
                                             "be negative')"}
    def test_get_projects_errors_500(self, application):
        with patch('app.routers.rest.projects.get_projects') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects")
            assert response.status_code == 500

    def test_get_one_project(self, application):
        response = application.get("/api/v1/projects/test")
        assert response.status_code == 200
        assert response.json() == {'archived': [], 'current': [], 'future': [], 'name': 'test'}