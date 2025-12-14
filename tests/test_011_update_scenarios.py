# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

def test_update_scenario(application, logged):
    response = application.put(
        "/api/v1/projects/default/epics/default/features/default/scenarios/default",
        headers=logged,
        json={"name": "New name", "tags": "new tags", "steps": "new steps"},
    )
    assert response.status_code == 204

    response = application.get(
        "/api/v1/projects/default/epics/default/features/default/scenarios/default",
        headers=logged,
    )
    assert response.status_code == 200
    scenario = response.json()
    assert scenario["name"] == "New name"
    assert scenario["tags"] == "new tags"
    assert scenario["steps"] == "new steps"


def test_update_scenario_not_found(application, logged):
    response = application.put(
        "/api/v1/projects/default/epics/default/features/default/scenarios/not-found",
        headers=logged,
        json={"name": "New name"},
    )
    assert response.status_code == 404


def test_update_scenario_no_auth(application):
    response = application.put(
        "/api/v1/projects/default/epics/default/features/default/scenarios/default",
        json={"name": "New name"},
    )
    assert response.status_code == 401


def test_update_scenario_no_params(application, logged):
    response = application.put(
        "/api/v1/projects/default/epics/default/features/default/scenarios/default",
        headers=logged,
        json={},
    )
    assert response.status_code == 422
