import re
from unittest.mock import patch

import pytest

from app.app_exception import DuplicateProject, ProjectNameInvalid
from app.database.postgre.projects.pg_projects import validate_project_name


@pytest.mark.path("/projects/management")
@pytest.mark.test_steps(
    "Given project name 'test' is provided",
    "When the project name is validated by 'validate_project_name'",
    "Then 'validate_project_name' returns None",
)
@pytest.mark.tags("projects", "mandatory")
@pytest.mark.description("""Well formed project name passes the validation.
Length <= 63
No "\\", "/", "$" characters
Not the unique character '*'""")
def test_project_name_valid_return_none() -> None:
    assert validate_project_name("test") is None, "error validating project name 'test'"


fail_projects = [
    pytest.param(
        "te/st",
        "Project name must not contain \\ / $ characters",
        marks=[
            pytest.mark.test_steps(
                "Given project name 'te/st' is provided",
                "When the project name is validated by 'validate_project_name'",
                "Then 'validate_project_name' raises ProjectNameInvalid error",
            ),
            pytest.mark.description("Validate that '/' character is not allowed"),
        ],
    ),
    pytest.param(
        "te\\st",
        "Project name must not contain \\ / $ characters",
        marks=[
            pytest.mark.test_steps(
                "Given project name 'te\\st' is provided",
                "When the project name is validated by 'validate_project_name'",
                "Then 'validate_project_name' raises ProjectNameInvalid error",
            ),
            pytest.mark.description("Validate that '\\' character is not allowed"),
        ],
    ),
    pytest.param(
        "te$st",
        "Project name must not contain \\ / $ characters",
        marks=[
            pytest.mark.test_steps(
                "Given project name 'te$st' is provided",
                "When the project name is validated by 'validate_project_name'",
                "Then 'validate_project_name' raises ProjectNameInvalid error",
            ),
            pytest.mark.description("Validate that '$' character is not allowed"),
        ],
    ),
    pytest.param(
        "longlonglonglonglonglonglonglonglonglonglonglonglonglonglonglong",
        "Project name must be strictly less than 64 character",
        marks=[
            pytest.mark.test_steps(
                "Given project name 'longlonglonglonglonglonglonglonglonglonglonglonglonglonglonglong' is provided",
                "When the project name is validated by 'validate_project_name'",
                "Then 'validate_project_name' raises ProjectNameInvalid error",
            ),
            pytest.mark.description("Validate that project name cannot be more than 63 characters"),
        ],
    ),
    pytest.param(
        "*",
        "Project name must be different from '*' special project",
        marks=[
            pytest.mark.test_steps(
                "Given project name '*' is provided",
                "When the project name is validated by 'validate_project_name'",
                "Then 'validate_project_name' raises ProjectNameInvalid error",
            ),
            pytest.mark.description("Validate that '*' project name is not allowed"),
        ],
    ),
]


@pytest.mark.path("/projects/management")
@pytest.mark.tags("projects", "create", "error")
@pytest.mark.parametrize("project_name,error_message", fail_projects)
def test_projects_invalid_raises_exception(project_name: str, error_message: str) -> None:
    with pytest.raises(ProjectNameInvalid, match=re.escape(error_message)):
        validate_project_name(project_name)


@pytest.mark.path("/projects/management")
@pytest.mark.test_steps(
    "Given project name 'test' exists",
    "Given project name 'test' is provided",
    "When the project name is validated by 'validate_project_name'",
    "Then 'validate_project_name' raises DuplicateProject error",
)
@pytest.mark.tags("projects", "create", "error")
@pytest.mark.description("Cannot create duplicate project")
def test_projects_duplicate_raises_exception() -> None:
    with pytest.raises(
        DuplicateProject,
        match=re.escape(
            "Project name 'test' already exists. Please update the name so that project can be registered."
        ),
    ):
        with patch("app.database.postgre.projects.pg_projects.contains") as contains_mock:
            contains_mock.return_value = True
            validate_project_name("test")
        validate_project_name("test")
