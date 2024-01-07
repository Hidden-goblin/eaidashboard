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


