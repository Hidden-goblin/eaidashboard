# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest

from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.status_enum import BugStatusEnum


class TestRestBug:
    project_name = "test_bug"
    current_version = "1.0.0"
    previous_version = "0.9.0"
    next_version = "1.1.0"

    def test_setup(self, application, logged):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        response = application.post("/api/v1/settings/projects",
                                    json={"name": TestRestBug.project_name},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/versions",
                                    json={"version": TestRestBug.current_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/versions",
                                    json={"version": TestRestBug.previous_version},
                                    headers=logged)
        assert response.status_code == 200
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/versions",
                                    json={"version": TestRestBug.next_version},
                                    headers=logged)
        assert response.status_code == 200

    def test_get_bugs_from_version(self, application):
        response = application.get(
            f"/api/v1/projects/{TestRestBug.project_name}/versions/"
            f"{TestRestBug.previous_version}/bugs")
        assert response.status_code == 200
        assert response.json() == []

    fake_project_version = [(project_name, "5.0.0", "Version '5.0.0' is not found"),
                            ("unknown", current_version, "'unknown' is not registered"),
                            ("unknown", "5.0.0", "'unknown' is not registered")]

    @pytest.mark.parametrize("project_name,version,message", fake_project_version)
    def test_get_bugs_from_version_error_404(self, application, project_name, version, message):
        response = application.get(
            f"/api/v1/projects/{project_name}/versions/"
            f"{version}/bugs")
        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_get_bugs_from_version_error_500(self, application):
        with patch('app.routers.rest.bugs.db_g_bugs') as rp:
            rp.side_effect = Exception("error")
            response = application.get(
                f"/api/v1/projects/{TestRestBug.project_name}/versions/"
                f"{TestRestBug.previous_version}/bugs")
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_get_bugs_from_project(self, application):
        response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_bugs_from_project_error_404(self, application):
        response = application.get("/api/v1/projects/unknown/bugs")
        assert response.status_code == 404
        assert response.json()['detail'] == "'unknown' is not registered"

    def test_get_bugs_from_project_error_500(self, application):
        with patch('app.routers.rest.bugs.db_g_bugs') as rp:
            rp.side_effect = Exception("error")
            response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs")
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_create_bug_error_401(self, application):
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                    json={"version": f"{TestRestBug.current_version}",
                                          "title": "first bug",
                                          "description": "lorem ipsum dolor",
                                          "url": ""})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    create_error_404 = [("unknown", {"title": "First bug",
                                     "version": current_version,
                                     "description": "Desc"}, "'unknown' is not registered"),
                        (project_name, {"title": "First bug",
                                        "version": "5.0.0",
                                        "description": "Desc"}, "Version '5.0.0' is not found"),
                        ("unknown", {"title": "First bug",
                                     "version": "5.0.0",
                                     "description": "Desc"}, "'unknown' is not registered")]

    @pytest.mark.parametrize("project_name,payload,message", create_error_404)
    def test_create_bug_error_404(self, application, logged, project_name, payload, message):
        response = application.post(f"/api/v1/projects/{project_name}/bugs",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 404
        assert response.json()["detail"] == message

    payload_error_422 = [({}, [{'loc': ['body', 'version'],
                                'msg': 'field required',
                                'type': 'value_error.missing'},
                               {'loc': ['body', 'title'],
                                'msg': 'field required',
                                'type': 'value_error.missing'},
                               {'loc': ['body', 'description'],
                                'msg': 'field required',
                                'type': 'value_error.missing'}
                               ]),
                         ({"version": "1.0.0"}, [{'loc': ['body', 'title'],
                                                  'msg': 'field required',
                                                  'type': 'value_error.missing'},
                                                 {'loc': ['body', 'description'],
                                                  'msg': 'field required',
                                                  'type': 'value_error.missing'}
                                                 ]),
                         ({"version": f"{current_version}",
                           "title": "First bug",
                           "description": "Not to be created",
                           "comment": "mine"}, [{'loc': ['body', 'comment'],
                                                 'msg': 'extra fields not permitted',
                                                 'type': 'value_error.extra'}])]

    @pytest.mark.parametrize("payload,message", payload_error_422)
    def test_create_bug_error_422(self, application, logged, payload, message):
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 422
        assert all(msg in message for msg in response.json()["detail"])

    def test_create_bug_error_500(self, application, logged):
        with patch('app.routers.rest.bugs.insert_bug') as rp:
            rp.side_effect = Exception("error")
            response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                        json={"title": "First",
                                              "version": TestRestBug.current_version,
                                              "description": "First, only mandatory field"},
                                        headers=logged)
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    create_payload = [({"title": "First",
                        "version": current_version,
                        "description": "First, only mandatory field"}, 1),
                      ({"title": "Second",
                        "version": current_version,
                        "criticality": "minor",
                        "description": "Second, with criticality set"}, 2),
                      ({"title": "Third",
                        "version": current_version,
                        "url": "no check on url",
                        "description": "Third, with url set"}, 3)
                      ]

    @pytest.mark.parametrize("payload,inserted_id", create_payload)
    def test_create_bug(self, application, logged, payload, inserted_id):
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 200
        assert response.json()["inserted_id"] == str(inserted_id)

    duplicate_error = [({"title": "Third",
                         "version": current_version,
                         "description": "Third (duplicate),only mandatory"},
                        (
                            f"Cannot insert existing bug for '{project_name}', "
                            f"'{current_version}', 'Third'.\nPlease check your data.")
                        ),
                       # ({"title": "third",
                       #   "version": current_version,
                       #   "description": "Third (duplicate),only mandatory"},
                       #  (
                       #      f"Cannot insert existing bug for '{project_name}', "
                       #      f"'{current_version}', 'third'.\nPlease check your data.")
                       #  )
                       ]

    @pytest.mark.parametrize("payload,message", duplicate_error)
    def test_create_bug_error_409(self, application, logged, payload, message):
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 409
        assert response.json()["detail"] == message

    populate_bug = [{"title": "First-past",
                     "version": previous_version,
                     "description": "First, only mandatory field"},
                    {"title": "Second-past",
                     "version": previous_version,
                     "criticality": "minor",
                     "description": "Second, with criticality set"},
                    {"title": "Third-past",
                     "version": previous_version,
                     "criticality": "blocking",
                     "description": "Third, with criticality set"},
                    {"title": "First-past",
                     "version": next_version,
                     "description": "First, only mandatory field"},
                    {"title": "Second-past",
                     "version": next_version,
                     "criticality": "minor",
                     "description": "Second, with criticality set"},
                    {"title": "Third-past",
                     "version": next_version,
                     "criticality": "blocking",
                     "description": "Third, with criticality set"}
                    ]

    @pytest.mark.parametrize("payload", populate_bug)
    def test_create_bug_populate(self, application, logged, payload):
        response = application.post(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                    json=payload,
                                    headers=logged)
        assert response.status_code == 200

    def test_get_bugs_from_version_populated(self, application):
        response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs")
        assert response.status_code == 200
        assert len(response.json()) == 9

    bugs_project_filter = [({"status": [BugStatusEnum.fix_ready.value,
                                        BugStatusEnum.closed.value]}, 0),
                           ({"criticality": BugCriticalityEnum.major.value}, 4)]

    @pytest.mark.parametrize("payload,count", bugs_project_filter)
    def test_get_bugs_from_version_filter(self, application, payload, count):
        response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs",
                                   params=payload)
        assert response.status_code == 200
        assert len(response.json()) == count

    def test_get_bug(self, application):
        response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs/1")
        assert response.status_code == 200
        assert response.json()["title"] == "First"
        assert response.json()["version"] == TestRestBug.current_version
        assert response.json()["description"] == "First, only mandatory field"
        assert response.json()["url"] == ""
        assert response.json()["criticality"] == "major"
        assert response.json()["status"] == "open"
        assert response.json()["created"] == response.json()["updated"]

    def test_get_bug_internal_id_not_found(self, application):
        response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs/100")

        assert response.status_code == 404
        assert response.json()["detail"] == "Bug '100' is not found."

    def test_get_bug_error_404(self, application):
        response = application.get("/api/v1/projects/unknown/bugs/1")

        assert response.status_code == 404
        assert response.json()["detail"] == "'unknown' is not registered"

    def test_get_bug_error_500(self, application):
        with patch('app.routers.rest.bugs.db_get_bug') as rp:
            rp.side_effect = Exception("error")
            response = application.get(f"/api/v1/projects/{TestRestBug.project_name}/bugs/1")

            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_update_bug_error_401(self, application):
        response = application.put(f"/api/v1/projects/{TestRestBug.project_name}/bugs/1",
                                   json={"title": "First updated"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    update_bug_404 = [("unknown", "1", {"title": "First updated"}, "'unknown' is not registered"),
                      (project_name, "100", {"title": "First updated"}, "Bug '100' is not found."),
                      (
                      project_name, "1", {"version": "6.6.6"}, "The version '6.6.6' is not found.")]

    @pytest.mark.parametrize("project_name,bug_id,payload,message", update_bug_404)
    def test_update_bug_error_404(self,
                                  application,
                                  logged,
                                  project_name,
                                  bug_id,
                                  payload,
                                  message):
        response = application.put(f"/api/v1/projects/{project_name}/bugs/{bug_id}",
                                   json=payload,
                                   headers=logged)

        assert response.status_code == 404
        assert response.json()["detail"] == message

    def test_update_bug_error_422(self, application, logged):
        response = application.put(f"/api/v1/projects/{TestRestBug.project_name}/bugs/1",
                                   json={"status": "reopen"},
                                   headers=logged)

        assert response.status_code == 422
        assert response.json()["detail"] == [
            {'ctx': {'enum_values': ['open', 'closed', 'closed not a defect', 'fix ready']},
             'loc': ['body', 'status'],
             'msg': "value is not a valid enumeration member; permitted: 'open', 'closed', "
                    "'closed not a defect', 'fix ready'",
             'type': 'type_error.enum'}]

    def test_update_bug_error_500(self, application, logged):
        with patch('app.routers.rest.bugs.db_update_bugs') as rp:
            rp.side_effect = Exception("error")
            response = application.put(f"/api/v1/projects/{TestRestBug.project_name}/bugs/1",
                                       json={"title": "First updated"},
                                       headers=logged)
            assert response.status_code == 500
            assert response.json()["detail"] == "error"

    def test_update_bug(self, application, logged):
        response = application.put(f"/api/v1/projects/{TestRestBug.project_name}/bugs/1",
                                   json={"title": "First updated"},
                                   headers=logged)
        assert response.status_code == 200
        assert response.json()["criticality"] == "major"
        assert response.json()["description"] == "First, only mandatory field"
        assert response.json()["status"] == "open"
        assert response.json()["title"] == "First updated"
        assert response.json()["url"] == ""
        assert response.json()["version"] == "1.0.0"