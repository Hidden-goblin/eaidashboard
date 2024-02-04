# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

class TestRestRepository:
    project_name = "test_repository"

    def test_setup(self, application, logged):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        response = application.post("/api/v1/settings/projects",
                                    json={"name": TestRestRepository.project_name},
                                    headers=logged)
        assert response.status_code == 200

    def test_upload_repository(self, application, logged):
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                        files={'file': file},
                                        headers=logged)
            assert response.status_code == 204

    def test_upload_repository_error_404_project_not_found(self, application, logged):
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post("/api/v1/projects/unknown/repository",
                                        files={'file': file},
                                        headers=logged)
            assert response.status_code == 404

    def test_upload_repository_error_400_malformed_csv(self, application, logged):
        with open("tests/resources/repository_as_csv_malformed.csv", "rb") as file:
            response = application.post(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                        files={'file': file},
                                        headers=logged)
            assert response.status_code == 400

    def test_upload_repository_error_401(self, application):
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                        files={'file': file})
            assert response.status_code == 401

    def test_retrieve_repository(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   headers=logged)
        assert response.status_code == 200

    def test_retrieve_repository_all_features(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "features"},
                                   headers=logged)
        assert response.status_code == 200

    def test_retrieve_repository_specific_features(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "features",
                                           "epic": "first_epic"},
                                   headers=logged)
        assert response.status_code == 200

    def test_retrieve_repository_non_existing_specific_features(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "features",
                                           "epic": "first_epc"},
                                   headers=logged)
        assert response.status_code == 200

    def test_retrieve_repository_all_scenarios(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "scenarios"},
                                   headers=logged)
        assert response.status_code == 200
        assert len(response.json()) != 0

    def test_retrieve_repository_epic_specific_scenarios(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "scenarios",
                                           "epic": "first_epic"},
                                   headers=logged)
        assert response.status_code == 200
        assert len(response.json()) != 0

    def test_retrieve_repository_feature_specific_scenarios(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "scenarios",
                                           "feature": "New Test feature"},
                                   headers=logged)
        assert response.status_code == 200
        assert len(response.json()) != 0

    def test_retrieve_repository_feature_specific_scenarios_case_sensitive(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                                   params={"elements": "scenarios",
                                           "feature": "new test feature"},
                                   headers=logged)
        assert response.status_code == 200
        assert len(response.json()) == 0


    def test_retrieve_repository_error_404(self, application, logged):
        response = application.get(f"/api/v1/projects/unknown/repository",
                                   headers=logged)
        assert response.status_code == 404

    def test_retrieve_repository_error_401(self, application):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository")
        assert response.status_code == 401

    def test_retrieve_epics(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/epics",
                                   headers=logged)
        assert response.status_code == 200
        assert all(item in ['first_epic', 'second_epic'] for item in response.json())

    def test_retrieve_epics_error_404(self, application, logged):
        response = application.get("/api/v1/projects/unknown/epics",
                                   headers=logged)
        assert response.status_code == 404

    def test_retrieve_features(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/epics/first_epic/features",
                                   headers=logged)
        assert response.status_code == 200

    def test_retrieve_features_error_404_project(self, application, logged):
        response = application.get(f"/api/v1/projects/unknown/epics/first_epic/features",
                                   headers=logged)
        assert response.status_code == 404

    def test_retrieve_features_unknown_epic(self, application, logged):
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/epics/first_epc/features",
                                   headers=logged)
        assert response.status_code == 200
        assert response.json() == []
