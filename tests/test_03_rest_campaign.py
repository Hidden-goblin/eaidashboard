# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest


class TestRestCampaign:
    project_name = "test_campaign"
    current_version = "1.0.0"

    def test_setup(self, application, logged):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        response = application.post("/api/v1/settings/projects",
                                    json={"name": TestRestCampaign.project_name},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/versions",
                                    json={"version": TestRestCampaign.current_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/versions/"
                                    f"{TestRestCampaign.current_version}/tickets",
                                    json={"reference": "ref-001",
                                          "description": "Description 1"},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/versions/"
                                    f"{TestRestCampaign.current_version}/tickets",
                                    json={"reference": "ref-002",
                                          "description": "Description 2"},
                                    headers=logged)
        assert response.status_code == 200

    def test_get_campaigns(self, application):
        response = application.get("/api/v1/projects/test/campaigns")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_campaigns_errors_404(self, application):
        # project not found
        response = application.get("/api/v1/projects/toto/campaigns")
        assert response.status_code == 404
        assert response.json()["detail"] == "'toto' is not registered"

        # version not found
        response = application.get("/api/v1/projects/test/campaigns", params={"version": "3.0.0"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Version '3.0.0' is not found"

    def test_get_campaigns_errors_500(self, application):
        with patch('app.routers.rest.project_campaigns.retrieve_campaign') as rp:
            rp.side_effect = Exception("error")
            response = application.get("/api/v1/projects/test/campaigns")
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_create_campaigns_errors_401(self, application):
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                                    json={"version": TestRestCampaign.current_version})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_create_campaigns(self, application, logged):
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                                    json={"version": TestRestCampaign.current_version},
                                    headers=logged)
        assert response.status_code == 200
        assert response.json() == {"project_name": TestRestCampaign.project_name,
                                   "version": TestRestCampaign.current_version,
                                   "occurrence": 1,
                                   "description": None,
                                   "status": "recorded"}

    payload_error_422 = [({}, [{'loc': ['body', 'version'],
                                'msg': 'field required',
                                'type': 'value_error.missing'}]),
                         ({"version": "1.1.1",
                           "description": "desc"}, [{'loc': ['body', 'description'],
                                                     'msg': 'extra fields not permitted',
                                                     'type': 'value_error.extra'}])]

    @pytest.mark.parametrize("payload,message", payload_error_422)
    def test_create_campaigns_errors_422(self, application, logged, payload, message):
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 422
        assert response.json()["detail"] == message

    def test_create_campaigns_errors_404_project(self, application, logged):
        response = application.post("/api/v1/projects/unknown_project/campaigns",
                                    json={"version": TestRestCampaign.current_version},
                                    headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == "'unknown_project' is not registered"

    def test_create_campaigns_errors_404_version(self, application, logged):
        response = application.post(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                                    json={"version": "1.1.1"},
                                    headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == "Version '1.1.1' is not found"

    def test_create_campaigns_errors_500(self, application, logged):
        with patch('app.routers.rest.project_campaigns.create_campaign') as rp:
            rp.side_effect = Exception("error")
            response = application.post(
                f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns",
                json={"version": TestRestCampaign.current_version},
                headers=logged)
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_fill_campaign_errors_401(self, application):
        response = application.put(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns"
                                   f"/{TestRestCampaign.current_version}/1",
                                   json={"version": TestRestCampaign.current_version})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_fill_campaign(self, application, logged):
        response = application.put(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns"
                                   f"/{TestRestCampaign.current_version}/1",
                                   json={"ticket_reference": "ref-001"},
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == {"campaign_ticket_id": 1, "errors": []}

    def test_fill_campaign_200_no_error_on_duplicate(self, application, logged):
        response = application.put(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns"
                                   f"/{TestRestCampaign.current_version}/1",
                                   json={"ticket_reference": "ref-001"},
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == {"campaign_ticket_id": 1, "errors": []}

    campaign_error_404 = [
        ("unknown_project", "1.0.0", 1, "ref-002", "'unknown_project' is not registered"),
        (project_name, "0.0.0", 1, "ref-002", "Version '0.0.0' is not found"),
        (project_name, current_version, 3, "ref-002", "Occurrence '3' not found"),
        (project_name, current_version, 1, "ref-003",
         "Ticket 'ref-003' does not exist in project 'test_campaign' version '1.0.0'")]

    @pytest.mark.parametrize("project,version,occurrence,ticket, message", campaign_error_404)
    def test_fill_campaign_errors_404(self, application, logged, project, version, occurrence,
                                      ticket, message):
        response = application.put(f"/api/v1/projects/{project}/campaigns"
                                   f"/{version}/{occurrence}",
                                   json={"ticket_reference": ticket},
                                   headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_campaign(self, application):
        response = application.get(
            f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/"
            f"{TestRestCampaign.current_version}/1")
        assert response.status_code == 200
        assert response.json() == {"description": None,
                                   "status": "recorded",
                                   "project_name": "test_campaign",
                                   "occurrence": 1,
                                   "version": "1.0.0",
                                   "tickets": [{"reference": "ref-001",
                                                'scenarios': [],
                                                'status': 'open',
                                                'summary': 'Description 1'}]}

    get_campaign_errors_404 = [
        ("unknown_project", "1.0.0", 1, "'unknown_project' is not registered"),
        (project_name, "0.0.0", 1, "Version '0.0.0' is not found"),
        (project_name, current_version, 3, "Occurrence '3' not found")]

    @pytest.mark.parametrize("project,version,occurrence,message", get_campaign_errors_404)
    def test_get_campaign_errors_404(self, application, project, version, occurrence, message):
        response = application.get(f"/api/v1/projects/{project}/campaigns/{version}/{occurrence}")
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_campaign_errors_500(self, application):
        with patch('app.routers.rest.project_campaigns.get_campaign_content') as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/"
                f"{TestRestCampaign.current_version}/1")
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_patch_campaign_errors_401(self, application):
        response = application.patch(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/"
                                     f"{TestRestCampaign.current_version}/1",
                                     json={"status": "in progress", "description": "wonderful"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_patch_campaign(self, application, logged):
        response = application.patch(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/"
                                     f"{TestRestCampaign.current_version}/1",
                                     json={"status": "in progress", "description": "wonderful"},
                                     headers=logged)
        assert response.status_code == 200
        assert response.json() == {"project_name": "test_campaign",
                                   "version": "1.0.0",
                                   "occurrence": 1,
                                   "description": "wonderful",
                                   "status": "in progress"}

    def test_patch_campaign_errors_422(self, application, logged):
        response = application.patch(f"/api/v1/projects/{TestRestCampaign.project_name}/campaigns/"
                                     f"{TestRestCampaign.current_version}/1",
                                     json={"status": "progress", "description": "wonderful"},
                                     headers=logged)
        assert response.status_code == 422
        assert response.json()["detail"] == [{'loc': ['body', 'status'],
                                              'msg': "value is not a valid enumeration member; "
                                                     "permitted: 'recorded', 'in progress', "
                                                     "'cancelled', 'done', 'closed', 'paused'",
                                              'type': 'type_error.enum',
                                              'ctx': {'enum_values': ['recorded', 'in progress',
                                                                      'cancelled', 'done', 'closed',
                                                                      'paused']}}]
