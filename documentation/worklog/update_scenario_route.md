# Update Scenario Route

## Summary

This update introduces a new route to the REST API that allows updating a scenario.

## Changes

- Created a new route `PUT /api/v1/projects/:projectName/epics/:epicRef/features/:featureRef/scenarios/:scenarioRef` to update a scenario.
- The route is accessible only by authenticated users for the project.
- The fields that can be updated are `name`, `tags`, and `steps`.
- Created a Pydantic model `UpdateScenario` in `/app/schema/repository/scenario_schema.py`.
- Created the route in `/app/routers/rest/repository/rest_scenarios.py`.
- Updated the database interaction in `/app/database/postgre/test_repository/scenarios_utils.py`.
- Added tests for the new route in `/tests/test_011_update_scenarios.py`.
