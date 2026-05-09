# Testing Guide for eaidashboard

This guide provides comprehensive instructions on how to write and structure tests for the eaidashboard project. It covers both unit tests for individual functions and integration tests for API endpoints.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Unit Tests](#unit-tests)
3. [API Integration Tests](#api-integration-tests)
4. [Mocking Patterns](#mocking-patterns)
5. [Test Markers and Metadata](#test-markers-and-metadata)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## Test Structure

### Project Test Layout

```
tests/
├── conftest.py                 # Global pytest configuration and fixtures
├── test_000_auth.py           # Unit tests for authentication functions
├── test_000_rest_settings.py  # API integration tests for settings endpoints
├── test_001_rest_users.py     # API integration tests for user endpoints
├── test_00X_rest_*.py         # Pattern: API tests for different endpoints
├── resources/                 # Test data and fixtures
└── utils/                      # Test utilities and helpers
```

### Test File Naming Convention

- **Unit Tests**: `test_000_auth.py` - Tests for core functions and modules
- **API Tests**: `test_00X_rest_*.py` - Tests for REST API endpoints (where X is a sequence number)
- Start with test number 000 for authentication tests (foundation)
- Increment for other endpoints and features

### Test Scope

- **Function scope**: Tests are module-level functions (NOT classes)
- **Fixtures**: Session-level `application` fixture, function-level other fixtures
- **Execution order**: Controlled via `pytest-order` plugin

---

## Unit Tests

Unit tests verify individual functions in isolation by mocking all external dependencies (database, external services, etc.).

### Structure

```python
# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import AsyncMock, patch

import pytest

from app.database.authentication import authenticate_user
from app.schema.users import User

# noinspection PyUnresolvedReferences


# ==================== Section header for test grouping ====================


@pytest.mark.description("Human-readable test description")
@pytest.mark.tags("category", "subcategory", "status")
@pytest.mark.test_steps(
    "Given initial condition",
    "When action is performed",
    "Then expected outcome",
)
def test_function_name_happy_path() -> None:
    """Docstring explaining the test."""
    # Arrange
    test_data = "test_value"
    mock_user = User(username="user@example.com", scopes={"*": "admin"})

    with patch("app.database.authentication.get_user") as mock_get_user:
        mock_get_user.return_value = mock_user

        # Act
        result = function_under_test(test_data)

        # Assert
        assert result is not None
        mock_get_user.assert_called_once_with(test_data)
```

### Key Components

1. **Arrangement (Setup)**
   - Create test data
   - Initialize mock objects
   - Create test fixtures

2. **Action (Execution)**
   - Call the function under test
   - Pass mocked dependencies
   - Capture return value

3. **Assertion (Verification)**
   - Verify return values
   - Verify mock calls and parameters
   - Check side effects

### Mocking Database Interactions

When testing functions that interact with the database, mock the database access functions:

```python
def test_authenticate_user_valid_credentials() -> None:
    """Test successful authentication with valid username and password."""
    # Arrange
    test_username = "user@example.com"
    test_password = "correct_password"
    mock_user = User(username=test_username, scopes={"*": "admin"})

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            mock_get_user.return_value = mock_user
            mock_verify.return_value = (True, None)

            # Act
            result = authenticate_user(test_username, test_password)

            # Assert
            assert result is not None
            assert result.username == test_username
```

### Error Path Testing

Always test error scenarios with dedicated test functions:

```python
@pytest.mark.description("Test function with non-existing resource")
@pytest.mark.tags("category", "error_path")
@pytest.mark.test_steps(
    "Given resource does not exist",
    "When function is called",
    "Then None is returned",
)
def test_authenticate_user_non_existing_user() -> None:
    """Test authentication fails when user does not exist."""
    # Arrange
    with patch("app.database.authentication.get_user") as mock_get_user:
        mock_get_user.side_effect = Exception("User not found")

        # Act
        result = authenticate_user("nonexistent@example.com", "password")

        # Assert
        assert result is None
```

---

## API Integration Tests

API tests verify HTTP endpoints by calling them through the test client and mocking only the authorization layer (not the entire database).

### Structure

```python
# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

# noinspection PyUnresolvedReferences


@pytest.mark.description("Test API endpoint without authentication")
@pytest.mark.tags("endpoint", "get", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user calls the endpoint",
    "Then user gets 401 Unauthorized",
)
def test_endpoint_error_401(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.get("/api/v1/some/endpoint")
    assert response.status_code == 401


@pytest.mark.description("Test API endpoint with successful request")
@pytest.mark.tags("endpoint", "get", "mandatory")
@pytest.mark.test_steps(
    "Given user is authenticated",
    "When user calls the endpoint",
    "Then user gets 200 OK",
)
def test_endpoint_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 200 when user is authenticated."""
    response = application.get("/api/v1/some/endpoint", headers=logged_setting)
    assert response.status_code == 200
```

### Key Differences from Unit Tests

1. **Use `application` fixture**: The Flask/FastAPI test client
2. **Use `logged_setting` fixture**: Pre-configured authentication headers
3. **Make actual HTTP calls**: Use `application.get()`, `application.post()`, etc.
4. **Test full flow**: Authorization + endpoint logic
5. **Mock only specific layers**: Mock business logic, not authorization

---

## Mocking Patterns

### Pattern 0: Mocking Async Functions (IMPORTANT)

When mocking async functions (functions defined with `async def`), you **MUST** use `AsyncMock` instead of regular mocks. Otherwise, the `await` call in the actual code will fail.

#### Incorrect Pattern ❌

```python
# DON'T do this with async functions:
with patch("app.routers.rest.settings.settings.register_project") as rp:
    rp.return_value = "project_name"  # This won't work with await!
```

#### Correct Pattern ✅

```python
# Import AsyncMock
from unittest.mock import AsyncMock, patch

# Use new_callable=AsyncMock for async functions:
with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock) as rp:
    rp.return_value = "project_name"  # Now this works with await!
```

#### Async Function Mocking Examples

**With return value:**
```python
def test_create_projects_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test successful project creation."""
    project_name = "test_project"
    
    with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock, return_value=project_name):
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": project_name},
            headers=logged_setting,
        )
        assert response.status_code == 200
```

**With side_effect (exception):**
```python
def test_create_projects_duplicate_error(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test project creation fails when project exists."""
    with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock) as rp:
        rp.side_effect = DuplicateProject("Project already exists")
        
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": "existing_project"},
            headers=logged_setting,
        )
        assert response.status_code == 409
```

**With assertions about async calls:**
```python
def test_register_project_called_correctly(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test that register_project is called with correct arguments."""
    project_name = "new_project"
    
    with patch("app.routers.rest.settings.settings.register_project", new_callable=AsyncMock, return_value=project_name) as mock_register:
        response = application.post(
            "/api/v1/settings/projects",
            json={"name": project_name},
            headers=logged_setting,
        )
        
        assert response.status_code == 200
        # Verify the async function was called correctly
        mock_register.assert_called_once_with(project_name)
```

#### Key Rules for Async Mocking

1. **Always use `new_callable=AsyncMock`** when mocking async functions
2. **Both `return_value` and `side_effect` work** the same as with regular mocks
3. **Assertions like `assert_called_once()` still work** as expected
4. **Forget to use `AsyncMock`?** You'll get errors like "object is not awaitable"

### Pattern 1: Security Mocking with `mock_security` and `logged_setting`

The `mock_security` fixture is a factory function that overrides the `authorize_user` dependency at the FastAPI level. This prevents actual token validation while simulating authenticated requests.

#### Using `logged_setting` (Default Admin)

```python
def test_endpoint_authenticated(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """logged_setting provides default admin user headers."""
    response = application.get(
        "/api/v1/endpoint",
        headers=logged_setting,  # Contains Authorization header with test token
    )
    assert response.status_code == 200
```

#### Using `mock_security` (Custom Configuration)

```python
def test_endpoint_with_custom_user(
    application: Generator[TestClient, Any, None],
    mock_security: Callable[..., dict[str, str]],
) -> None:
    """mock_security allows customizing user properties."""
    # Setup custom user
    headers = mock_security(
        username="custom@example.com",
        scopes={"project1": "admin", "project2": "user"}
    )
    
    response = application.get(
        "/api/v1/endpoint",
        headers=headers,
    )
    assert response.status_code == 200
```

#### Using `mock_security` (Testing Authorization Errors)

```python
def test_endpoint_authorization_error(
    application: Generator[TestClient, Any, None],
    mock_security: Callable[..., dict[str, str]],
) -> None:
    """Test endpoint returns 403 when user lacks permission."""
    # Setup user without required scope
    headers = mock_security(
        username="user@example.com",
        scopes={"project1": "user"}  # No admin access
    )
    
    response = application.get(
        "/api/v1/admin/endpoint",
        headers=headers,
    )
    assert response.status_code == 403
```

#### Using `mock_security` (Testing Authentication Errors)

```python
def test_endpoint_authentication_error(
    application: Generator[TestClient, Any, None],
    mock_security: Callable[..., dict[str, str]],
) -> None:
    """Test endpoint returns 401 when token is invalid."""
    # Setup to raise authentication error
    headers = mock_security(status_code=401)
    
    response = application.get(
        "/api/v1/endpoint",
        headers=headers,
    )
    assert response.status_code == 401
```

### Pattern 2: Business Logic Mocking with `patch`

Mock business logic functions to test endpoint behavior without hitting the database:

```python
def test_endpoint_with_mocked_logic(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint with mocked business logic (async function)."""
    # For async functions, ALWAYS use new_callable=AsyncMock
    with patch("app.routers.rest.users.get_users", new_callable=AsyncMock) as mock_get_users:
        # Setup mock to return test data
        mock_get_users.return_value = [
            {"username": "user1@example.com", "scopes": {"*": "admin"}},
            {"username": "user2@example.com", "scopes": {"*": "user"}},
        ]
        
        # Call endpoint
        response = application.get(
            "/api/v1/users",
            headers=logged_setting,
        )
        
        # Verify result
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_get_users.assert_called_once()
```

**Important**: If the mocked function is async (defined with `async def`), you MUST use `new_callable=AsyncMock`. See Pattern 0 for details.

### Pattern 3: Exception Handling Testing

```python
def test_endpoint_with_exception(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint error handling when business logic fails (async function)."""
    # For async functions, use new_callable=AsyncMock
    with patch("app.routers.rest.users.get_users", new_callable=AsyncMock) as mock_get_users:
        # Setup mock to raise exception
        mock_get_users.side_effect = Exception("Database connection error")
        
        # Call endpoint
        response = application.get(
            "/api/v1/users",
            headers=logged_setting,
        )
        
        # Verify error response
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
```

---

## Test Markers and Metadata

All tests use pytest markers to enable filtering and reporting. These markers are also collected for integration with test reporting systems.

### Available Markers

```python
@pytest.mark.description("Human-readable test description")
@pytest.mark.tags("tag1", "tag2", "status")
@pytest.mark.test_steps(
    "Given precondition",
    "When action",
    "Then result",
)
def test_example() -> None:
    pass
```

### Marker Definitions

- **`@pytest.mark.description(text)`**: Human-readable description of what the test verifies
- **`@pytest.mark.tags(*tags)`**: Categorization tags for filtering tests
  - Common tags: `auth`, `users`, `projects`, `error`, `happy_path`, `error_path`
  - HTTP status tags: `401`, `403`, `404`, `422`, `500`, etc.
- **`@pytest.mark.test_steps(*steps)`**: BDD-style test steps for documentation
  - Format: "Given...", "When...", "Then..."

### Example Tag Combinations

```python
# Happy path test
@pytest.mark.tags("users", "create", "happy_path")

# Error path test
@pytest.mark.tags("users", "create", "error_path", "401")

# API status test
@pytest.mark.tags("authentication", "mandatory")

# Specific error handling
@pytest.mark.tags("projects", "delete", "error", "404")
```

---

## Best Practices

### 1. **Use Module-Level Functions, Not Classes**

✅ **DO:**
```python
def test_authenticate_user_valid() -> None:
    pass

def test_authenticate_user_invalid() -> None:
    pass
```

❌ **DON'T:**
```python
class TestAuthenticateUser:
    def test_authenticate_user_valid(self) -> None:
        pass
```

### 2. **Mock at the Right Level**

- **Unit tests**: Mock all external dependencies (DB, services)
- **Integration tests**: Mock authorization, but let endpoint logic run

### 3. **Use Descriptive Test Names**

```python
# Good: Function name clearly describes what is tested
def test_authenticate_user_with_valid_credentials() -> None:
    pass

# Less clear: Vague function name
def test_auth() -> None:
    pass
```

### 4. **Follow AAA Pattern**

- **Arrange**: Set up test data and mocks
- **Act**: Execute the code under test
- **Assert**: Verify results and mock calls

### 5. **Test Both Happy and Error Paths**

For every successful scenario, include corresponding error scenarios:

```python
# Happy path
def test_create_user_success() -> None:
    pass

# Error paths
def test_create_user_duplicate() -> None:
    pass

def test_create_user_invalid_email() -> None:
    pass

def test_create_user_unauthorized() -> None:
    pass
```

### 6. **Use Appropriate Fixtures**

```python
# Session-level: Created once per test session
application: Generator[TestClient, Any, None]

# Function-level: Created for each test
logged_setting: dict[str, str]
mock_security: Callable[..., dict[str, str]]
```

### 7. **Cover Edge Cases**

```python
# Simple cases
def test_with_valid_input() -> None:
    pass

# Edge cases
def test_with_empty_input() -> None:
    pass

def test_with_very_long_input() -> None:
    pass

def test_with_special_characters() -> None:
    pass
```

### 8. **Verify Mock Interactions**

```python
def test_function_calls_dependency() -> None:
    with patch("module.dependency") as mock_dep:
        mock_dep.return_value = "result"
        
        result = function_under_test()
        
        # Verify the mock was called correctly
        mock_dep.assert_called_once_with("expected_arg")
        assert result == "result"
```

### 9. **Keep Tests Isolated**

- Each test should be independent
- Don't rely on test execution order
- Clean up after tests using `autouse` fixtures if needed

### 10. **Use Parametrize for Multiple Scenarios**

```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid.email.com", False),
    ("", False),
])
def test_email_validation(input: str, expected: bool) -> None:
    assert validate_email(input) == expected
```

---

## Examples

### Example 1: Unit Test for Database Function

**File**: `tests/test_000_auth.py`

```python
from unittest.mock import patch
import pytest
from app.database.authentication import authenticate_user
from app.schema.users import User


@pytest.mark.description("Authenticate user with valid credentials")
@pytest.mark.tags("auth", "authenticate_user", "happy_path")
@pytest.mark.test_steps(
    "Given a user exists in the database",
    "When authenticate_user is called with correct credentials",
    "Then the User object is returned",
)
def test_authenticate_user_valid_credentials() -> None:
    """Test successful authentication with valid username and password."""
    # Arrange
    test_username = "user@example.com"
    test_password = "correct_password"
    mock_user = User(username=test_username, scopes={"*": "admin"})

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            mock_get_user.return_value = mock_user
            mock_verify.return_value = (True, None)

            # Act
            result = authenticate_user(test_username, test_password)

            # Assert
            assert result is not None
            assert result.username == test_username
            mock_get_user.assert_called_once_with(test_username, False)
            mock_verify.assert_called_once_with(test_password, mock_user["password"])


@pytest.mark.description("Authenticate user with wrong password")
@pytest.mark.tags("auth", "authenticate_user", "error_path")
@pytest.mark.test_steps(
    "Given a user exists in the database",
    "When authenticate_user is called with wrong password",
    "Then None is returned",
)
def test_authenticate_user_wrong_password() -> None:
    """Test authentication fails when password is incorrect."""
    # Arrange
    mock_user = User(username="user@example.com", scopes={"*": "user"})

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            mock_get_user.return_value = mock_user
            mock_verify.return_value = (False, None)

            # Act
            result = authenticate_user("user@example.com", "wrong_password")

            # Assert
            assert result is None
```

### Example 2: API Integration Test

**File**: `tests/test_000_rest_settings.py`

```python
from typing import Any, Generator
from unittest.mock import AsyncMock, patch
import pytest
from starlette.testclient import TestClient


@pytest.mark.description("Retrieve project list when authenticated")
@pytest.mark.tags("projects", "get", "mandatory")
@pytest.mark.test_steps(
    "Given admin is logged in",
    "When admin requests the project list",
    "Then admin gets 200 OK with project list",
)
def test_get_projects_success(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test retrieving projects with valid authentication."""
    # Use AsyncMock for async functions
    with patch("app.routers.rest.settings.settings.registered_projects", new_callable=AsyncMock) as mock_get:
        # Arrange
        mock_get.return_value = ["project1", "project2"]
        
        # Act
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged_setting,
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == ["project1", "project2"]



@pytest.mark.description("Get projects without authentication")
@pytest.mark.tags("projects", "get", "error", "401")
@pytest.mark.test_steps(
    "Given user is not authenticated",
    "When user tries to get projects",
    "Then user gets 401 Unauthorized",
)
def test_get_projects_unauthorized(
    application: Generator[TestClient, Any, None],
) -> None:
    """Test endpoint returns 401 when user is not authenticated."""
    response = application.get("/api/v1/settings/projects")
    assert response.status_code == 401


@pytest.mark.description("Get projects when server error occurs")
@pytest.mark.tags("projects", "get", "error", "500")
@pytest.mark.test_steps(
    "Given admin is logged in",
    "Given a database error occurs",
    "When admin requests projects",
    "Then admin gets 500 Server Error",
)
def test_get_projects_server_error(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],
) -> None:
    """Test endpoint returns 500 when business logic fails."""
    # Use AsyncMock for async functions
    with patch("app.routers.rest.settings.settings.registered_projects", new_callable=AsyncMock) as mock_get:
        # Arrange
        mock_get.side_effect = Exception("Database error")
        
        # Act
        response = application.get(
            "/api/v1/settings/projects",
            headers=logged_setting,
        )
        
        # Assert
        assert response.status_code == 500
```

### Example 3: Custom Security Mocking

**File**: `tests/test_001_rest_users.py`

```python
def test_create_user_with_limited_scope(
    application: Generator[TestClient, Any, None],
    mock_security: Callable[..., dict[str, str]],
) -> None:
    """Test user with limited scope cannot create users."""
    # Setup user with "user" role instead of "admin"
    headers = mock_security(
        username="limited@example.com",
        scopes={"*": "user"}  # Limited scope
    )
    
    response = application.post(
        "/api/v1/users",
        json={"username": "new@example.com", "password": "pwd"},
        headers=headers,
    )
    
    # Expect 403 Forbidden
    assert response.status_code == 403


def test_create_user_authentication_failure(
    application: Generator[TestClient, Any, None],
    mock_security: Callable[..., dict[str, str]],
) -> None:
    """Test endpoint returns 401 when authentication fails."""
    # Setup to simulate authentication failure
    headers = mock_security(
        status_code=401,
        detail="Invalid token"
    )
    
    response = application.post(
        "/api/v1/users",
        json={"username": "new@example.com", "password": "pwd"},
        headers=headers,
    )
    
    assert response.status_code == 401
```

---

## Running Tests

### Run All Tests

```bash
python -m pytest tests/
```

### Run Specific Test File

```bash
python -m pytest tests/test_000_auth.py
```

### Run Tests with Specific Tag

```bash
python -m pytest tests/ -m "happy_path"
python -m pytest tests/ -m "error_path"
python -m pytest tests/ -m "401"
```

### Run Tests with Verbose Output

```bash
python -m pytest tests/test_000_auth.py -v
```

### Run Tests with Coverage

```bash
python -m coverage run -m pytest tests/
python -m coverage report
python -m coverage html
```

### Run Single Test Function

```bash
python -m pytest tests/test_000_auth.py::test_authenticate_user_valid_credentials -v
```

---

## Common Issues and Solutions

### Issue: Test fails with "Object is not awaitable"

**Problem**: Trying to mock an async function without using `AsyncMock`

**Solution**: Use `AsyncMock` from `unittest.mock` for async functions

```python
# Wrong:
with patch("app.database.async_function") as mock:
    mock.return_value = "result"  # ❌ TypeError: object is not awaitable

# Correct:
from unittest.mock import AsyncMock, patch

with patch("app.database.async_function", new_callable=AsyncMock) as mock:
    mock.return_value = "result"  # ✅ Works correctly with await
```

### Issue: Test fails with "Module not mocked"

**Problem**: External call made during test

**Solution**: Add `patch` for the external dependency

```python
with patch("app.database.authentication.get_user") as mock:
    mock.return_value = test_data
    # Test code here
```

### Issue: Security/Authorization not overridden

**Problem**: Using wrong headers or not using `logged_setting` fixture

**Solution**: Use `logged_setting` fixture for authenticated tests

```python
def test_endpoint(
    application: Generator[TestClient, Any, None],
    logged_setting: dict[str, str],  # Include this fixture
) -> None:
    response = application.get(
        "/api/v1/endpoint",
        headers=logged_setting,  # Add headers
    )
```

### Issue: Test order dependency

**Problem**: Tests pass individually but fail when run together

**Solution**: Ensure tests are independent; use fixtures for setup

```python
# Bad: Test depends on previous test running
def test_create_and_list():
    create()
    list()

# Good: Each test is independent
def test_create():
    create()

def test_list():
    # Setup data for list
    list()
```

---

## For AI Agents

### When Creating a New Test File

1. Check if the file follows naming convention `test_XXX_<feature>.py`
2. Import necessary modules and fixtures (including `AsyncMock` if testing async functions)
3. Add `# noinspection PyUnresolvedReferences` comment
4. Group related tests with section comments `# ======== ... ========`
5. Each test should be a module-level function (not a class)
6. Use `@pytest.mark` decorators for all metadata
7. Follow the AAA pattern (Arrange, Act, Assert)
8. Mock external dependencies at appropriate levels
9. Test both happy paths and error scenarios
10. Use `patch` for unit tests, `logged_setting` for API tests
11. **CRITICAL**: Use `AsyncMock` for async functions (see below)

### When Mocking Async Functions (CRITICAL)

**ALWAYS** use `AsyncMock` from `unittest.mock` when mocking async functions. Regular mocks will cause "object is not awaitable" errors.

```python
from unittest.mock import AsyncMock, patch

# CORRECT - For async functions:
with patch("app.routers.rest.settings.register_project", new_callable=AsyncMock) as mock:
    mock.return_value = "value"

# WRONG - Don't do this with async functions:
with patch("app.routers.rest.settings.register_project") as mock:
    mock.return_value = "value"  # ❌ Will fail: "object is not awaitable"
```

**Key patterns:**
- `with patch(..., new_callable=AsyncMock, return_value="value")`
- `with patch(..., new_callable=AsyncMock) as mock: mock.side_effect = Exception(...)`
- Works with `assert_called_once()` and other assertions

### When Mocking Database Access

- For unit tests: Mock database functions completely
- Pattern: `with patch("app.database.<module>.<function>", new_callable=AsyncMock) as mock:` (if async)
- For async functions: **ALWAYS use `new_callable=AsyncMock`**
- Set return values with `mock.return_value = ...`
- Set exceptions with `mock.side_effect = Exception(...)`
- Verify calls with `mock.assert_called_once_with(...)`

### When Testing API Endpoints

- Use `application` fixture for HTTP test client
- Use `logged_setting` for default authenticated headers
- Use `mock_security()` for custom authentication scenarios
- Mock business logic, not authorization
- Test all HTTP status codes: 200, 400, 401, 403, 404, 409, 422, 500
- Include markers for filtering: `tags`, `description`, `test_steps`

### Common Test Structure Template

```python
@pytest.mark.description("<What is being tested>")
@pytest.mark.tags("<category>", "<subcategory>", "<status>")
@pytest.mark.test_steps(
    "Given <initial state>",
    "When <action>",
    "Then <expected result>",
)
def test_<function_or_endpoint>_<scenario>() -> None:
    """<Docstring explaining the test>."""
    # Arrange: Set up test data and mocks
    
    with patch(...) as mock_...:
        # Act: Execute the code being tested
        
        # Assert: Verify results and mock calls
```


