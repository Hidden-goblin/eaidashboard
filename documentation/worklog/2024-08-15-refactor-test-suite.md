# 2024-08-15 - Refactor test suite to use temporary databases

## Summary

The test suite has been refactored to use temporary databases for PostgreSQL and Redis, removing the need for manually managed database instances. This was achieved by leveraging the `pytest-postgresql` and `pytest-redis` libraries to create temporary, real databases for the tests.

## Changes

- Added `pytest-postgresql` and `pytest-redis` to the development dependencies in `pyproject.toml`.
- Created a new `tests/conftest.py` file with fixtures to provide connections to the temporary databases.
- Created a new `tests/populate.py` file with a function to populate the temporary database with the required schema and data.
- Refactored the `application` fixture in `tests/conftest.py` to use the new temporary database fixtures.
- Removed the old database and Redis mocking logic from `tests/conftest.py`.
- Added a new test file `tests/test_database.py` with a comprehensive test for the database connection function.
- Installed `postgresql-client` and `redis-server` to provide the necessary executables for the temporary database fixtures.

## Benefits

- The tests no longer require manually managed database instances, making them easier to run and more reliable.
- The tests are now faster and more isolated, as they no longer depend on external services.
- The new testing infrastructure is more robust and easier to maintain.
