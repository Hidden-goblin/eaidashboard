# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

from starlette.testclient import TestClient

from tests.utils.context_manager import Context
from tests.utils.project_setting import set_project


# noinspection PyUnresolvedReferences
class TestRestRepository:
    project_name = "test_repository"
    second_project_name = "test.repository"
    context = Context()

    def test_setup(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        set_project(
            TestRestRepository.project_name,
            application,
            logged,
        )
        set_project(
            TestRestRepository.second_project_name,
            application,
            logged,
        )

    def test_upload_repository(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post(
                f"/api/v1/projects/{TestRestRepository.project_name}/repository",
                files={"file": file},
                headers=logged,
            )
            assert response.status_code == 204
            response = application.post(
                f"/api/v1/projects/{TestRestRepository.second_project_name}/repository",
                files={"file": file},
                headers=logged,
            )
            assert response.status_code == 204

    def test_upload_repository_error_404_project_not_found(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post(
                "/api/v1/projects/unknown/repository",
                files={"file": file},
                headers=logged,
            )
            assert response.status_code == 404

    def test_upload_repository_error_400_malformed_csv(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        with open("tests/resources/repository_as_csv_malformed.csv", "rb") as file:
            response = application.post(
                f"/api/v1/projects/{TestRestRepository.project_name}/repository", files={"file": file}, headers=logged
            )
            assert response.status_code == 400

    def test_upload_repository_error_401(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
    ) -> None:
        with open("tests/resources/repository_as_csv.csv", "rb") as file:
            response = application.post(
                f"/api/v1/projects/{TestRestRepository.project_name}/repository", files={"file": file}
            )
            assert response.status_code == 401

    def test_retrieve_repository(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository", headers=logged)
        assert response.status_code == 200

    def test_retrieve_repository_all_features(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "features"},
            headers=logged,
        )
        assert response.status_code == 200

    def test_retrieve_repository_specific_features(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "features", "epic": "first_epic"},
            headers=logged,
        )
        assert response.status_code == 200

    def test_retrieve_repository_non_existing_specific_features(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "features", "epic": "first_epc"},
            headers=logged,
        )
        assert response.status_code == 404, f"Expecting status code '404', get '{response.status_code}'"
        assert response.json() == {"detail": "Epic 'first_epc' not found in project 'test_repository'."}

    def test_retrieve_repository_all_scenarios(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "scenarios"},
            headers=logged,
        )
        assert response.status_code == 200
        assert len(response.json()) != 0
        TestRestRepository.context.set_context(f"{TestRestRepository.project_name}/scenarios", response.json())

    def test_retrieve_repository_epic_specific_scenarios(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "scenarios", "epic": "first_epic"},
            headers=logged,
        )
        assert response.status_code == 200
        assert len(response.json()) != 0

    def test_retrieve_repository_feature_specific_scenarios(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "scenarios", "feature": "New Test feature"},
            headers=logged,
        )
        assert response.status_code == 200
        assert len(response.json()) != 0

    def test_retrieve_repository_feature_specific_scenarios_case_sensitive(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/repository",
            params={"elements": "scenarios", "feature": "new test feature"},
            headers=logged,
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_retrieve_repository_error_404(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get("/api/v1/projects/unknown/repository", headers=logged)
        assert response.status_code == 404

    def test_retrieve_repository_error_401(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/repository")
        assert response.status_code == 401

    def test_retrieve_epics(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(f"/api/v1/projects/{TestRestRepository.project_name}/epics", headers=logged)
        assert response.status_code == 200
        assert all(item in ["first_epic", "second_epic"] for item in response.json())

    def test_retrieve_epics_error_404(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            "/api/v1/projects/unknown/epics",
            headers=logged,
        )
        assert response.status_code == 404

    def test_retrieve_features(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/epics/first_epic/features",
            headers=logged,
        )
        assert response.status_code == 200
        assert len(response.json()) == 2, (
            f"Should retrieve 2 features but get '{len(response.json())} from response\n {response.text}"
        )

    def test_retrieve_features_error_404_project(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            "/api/v1/projects/unknown/epics/first_epic/features",
            headers=logged,
        )
        assert response.status_code == 404

    def test_retrieve_features_unknown_epic(
        self: "TestRestRepository",
        application: Generator[TestClient, Any, None],
        logged: Generator[dict[str, str], Any, None],
    ) -> None:
        response = application.get(
            f"/api/v1/projects/{TestRestRepository.project_name}/epics/first_epc/features",
            headers=logged,
        )
        assert response.status_code == 404, f"Expecting status code 404, get {response.status_code}"
        assert response.json() == {"detail": "Epic 'first_epc' not found in project 'test_repository'."}
