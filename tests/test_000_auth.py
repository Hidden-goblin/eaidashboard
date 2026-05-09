# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from unittest.mock import patch

import pytest

from app.database.authentication import authenticate_user, create_access_token
from app.schema.authentication import TokenData
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.users import User

# noinspection PyUnresolvedReferences


# ==================== authenticate_user tests ====================


@pytest.mark.path("/authentication")
@pytest.mark.description("Test authenticate_user with valid credentials")
@pytest.mark.tags("auth", "authenticate_user", "mandatory")
@pytest.mark.test_steps(
    "Given a user exists in the database",
    "And the password hash is valid",
    "When authenticate_user is called with correct username and password",
    "Then the function returns the User object",
)
def test_authenticate_user_valid_credentials() -> None:
    """Test successful authentication with valid username and password."""
    # Arrange
    test_username = "user@example.com"
    test_password = "correct_password"
    mock_user = User(username=test_username, scopes={"*": "admin"}, password="hashed_correct_password")

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            with patch("app.database.authentication.maybe_update_password_hash") as mock_maybe_update:
                mock_get_user.return_value = mock_user
                mock_verify.return_value = (True, None)
                mock_maybe_update.return_value = mock_user

                # Act
                result = authenticate_user(test_username, test_password)

                # Assert
                assert result is not None
                assert result.username == test_username
                mock_get_user.assert_called_once_with(test_username, False)
                mock_verify.assert_called_once_with(test_password, mock_user["password"])


@pytest.mark.description("Test authenticate_user with non-existing user")
@pytest.mark.path("/authentication")
@pytest.mark.tags("auth", "authenticate_user", "error_path")
@pytest.mark.test_steps(
    "Given a user does not exist in the database",
    "When authenticate_user is called with a non-existing username",
    "Then the function returns None",
    "And an exception is logged",
)
def test_authenticate_user_non_existing_user() -> None:
    """Test authentication fails when user does not exist."""
    # Arrange
    test_username = "nonexistent@example.com"
    test_password = "any_password"

    with patch("app.database.authentication.get_user") as mock_get_user:
        mock_get_user.return_value = ApplicationError(
            error=ApplicationErrorCode.user_not_found,
            message="User not found",
        )

        # Act
        result = authenticate_user(test_username, test_password)

        # Assert
        assert result is None
        mock_get_user.assert_called_once_with(test_username, False)


@pytest.mark.description("Test authenticate_user with wrong password")
@pytest.mark.path("/authentication")
@pytest.mark.tags("auth", "authenticate_user", "error_path")
@pytest.mark.test_steps(
    "Given a user exists in the database",
    "And the provided password is incorrect",
    "When authenticate_user is called with correct username but wrong password",
    "Then the function returns None",
)
def test_authenticate_user_wrong_password() -> None:
    """Test authentication fails when password is incorrect."""
    # Arrange
    test_username = "user@example.com"
    test_password = "wrong_password"
    mock_user = User(username=test_username, scopes={"*": "user"}, password="hashed_correct_password")

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            mock_get_user.return_value = mock_user
            mock_verify.return_value = (False, None)

            # Act
            result = authenticate_user(test_username, test_password)

            # Assert
            assert result is None
            mock_get_user.assert_called_once_with(test_username, False)
            mock_verify.assert_called_once_with(test_password, mock_user["password"])


@pytest.mark.description("Test authenticate_user with hash update")
@pytest.mark.path("/authentication")
@pytest.mark.tags("auth", "authenticate_user", "hash_update")
@pytest.mark.test_steps(
    "Given a user exists in the database",
    "And the password verification indicates a new hash is needed",
    "When authenticate_user is called with valid credentials",
    "Then the function returns the User object",
    "And the password hash is updated",
)
def test_authenticate_user_with_hash_update() -> None:
    """Test successful authentication with password hash update."""
    # Arrange
    test_username = "user@example.com"
    test_password = "correct_password"
    new_hash = "new_bcrypt_hash"
    mock_user = User(username=test_username, scopes={"*": "admin"})

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            with patch("app.database.authentication.maybe_update_password_hash") as mock_maybe_update:
                mock_get_user.return_value = mock_user
                mock_verify.return_value = (True, new_hash)
                mock_maybe_update.return_value = mock_user

                # Act
                result = authenticate_user(test_username, test_password)

                # Assert
                assert result is not None
                assert result.username == test_username
                mock_maybe_update.assert_called_once_with(mock_user, new_hash, test_password)


@pytest.mark.description("Test authenticate_user with database exception")
@pytest.mark.path("/authentication")
@pytest.mark.tags("auth", "authenticate_user", "error_path")
@pytest.mark.test_steps(
    "Given a database error occurs",
    "When authenticate_user is called",
    "Then the function returns None",
    "And the exception is caught and logged",
)
def test_authenticate_user_database_exception() -> None:
    """Test authentication returns None when a database exception occurs."""
    # Arrange
    test_username = "user@example.com"
    test_password = "password"
    expected_exception_message = "Database connection error"

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.logging.getLogger") as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            mock_get_user.side_effect = Exception(expected_exception_message)

            # Act
            result = authenticate_user(test_username, test_password)

            # Assert
            assert result is None
            mock_logger.warning.assert_called_once_with(msg=expected_exception_message)


@pytest.mark.description("Test authenticate_user with verify_password exception")
@pytest.mark.path("/authentication")
@pytest.mark.tags("auth", "authenticate_user", "error_path")
@pytest.mark.test_steps(
    "Given a user exists in the database",
    "And password verification fails with an exception",
    "When authenticate_user is called",
    "Then the function returns None",
    "And the exception is caught and logged",
)
def test_authenticate_user_verify_password_exception() -> None:
    """Test authentication returns None when password verification fails."""
    # Arrange
    test_username = "user@example.com"
    test_password = "password"
    mock_user = User(username=test_username, scopes={"*": "user"})
    expected_exception_message = "Password verification error"

    with patch("app.database.authentication.get_user") as mock_get_user:
        with patch("app.database.authentication.verify_password") as mock_verify:
            with patch("app.database.authentication.logging.getLogger") as mock_get_logger:
                mock_logger = mock_get_logger.return_value
                mock_get_user.return_value = mock_user
                mock_verify.side_effect = Exception(expected_exception_message)

                # Act
                result = authenticate_user(test_username, test_password)

                # Assert
                assert result is None
                mock_logger.warning.assert_called_once_with(msg=expected_exception_message)


# ==================== create_access_token tests ====================


@pytest.mark.description("Test create_access_token with valid TokenData")
@pytest.mark.path("/authorization")
@pytest.mark.tags("auth", "create_access_token", "mandatory")
@pytest.mark.test_steps(
    "Given valid TokenData with username and scopes",
    "And register_connection returns True (token already registered)",
    "When create_access_token is called",
    "Then the function returns a JWT token string",
    "And the token is not empty",
)
def test_create_access_token_valid_data() -> None:
    """Test successful access token creation with valid TokenData."""
    # Arrange
    token_data = TokenData(sub="user@example.com", scopes={"*": "admin"})

    with patch("app.database.authentication.register_connection") as mock_register:
        with patch("app.database.authentication.conf") as mock_conf:
            with patch("app.database.authentication.encode") as mock_encode:
                mock_register.return_value = True
                mock_conf.SECRET_KEY = "test_secret_key"
                mock_conf.ALGORITHM = "HS256"
                expected_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
                mock_encode.return_value = expected_token

                # Act
                result = create_access_token(token_data)

                # Assert
                assert result == expected_token
                assert isinstance(result, str)
                mock_register.assert_called_once_with(token_data)
                mock_encode.assert_called_once()


@pytest.mark.description("Test create_access_token with generate_keys fallback")
@pytest.mark.tags("auth", "create_access_token", "mandatory")
@pytest.mark.test_steps(
    "Given valid TokenData with username and scopes",
    "And register_connection returns False (new connection needed)",
    "When create_access_token is called",
    "Then generate_keys is called to create new keys",
    "And the function returns a JWT token string",
)
def test_create_access_token_with_generate_keys() -> None:
    """Test access token creation triggers generate_keys when registration fails."""
    # Arrange
    token_data = TokenData(sub="user@example.com", scopes={"project1": "admin"})

    with patch("app.database.authentication.register_connection") as mock_register:
        with patch("app.database.authentication.generate_keys") as mock_generate:
            with patch("app.database.authentication.conf") as mock_conf:
                with patch("app.database.authentication.encode") as mock_encode:
                    mock_register.return_value = False
                    mock_conf.SECRET_KEY = "test_secret_key"
                    mock_conf.ALGORITHM = "HS256"
                    expected_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
                    mock_encode.return_value = expected_token

                    # Act
                    result = create_access_token(token_data)

                    # Assert
                    assert result == expected_token
                    mock_register.assert_called_once_with(token_data)
                    mock_generate.assert_called_once()
                    mock_encode.assert_called_once()


@pytest.mark.description("Test create_access_token with different scopes")
@pytest.mark.tags("auth", "create_access_token", "mandatory")
@pytest.mark.test_steps(
    "Given TokenData with multiple projects and different scopes",
    "When create_access_token is called for each user",
    "Then each generates a unique JWT token",
)
def test_create_access_token_multiple_scopes() -> None:
    """Test access token creation with multiple project scopes."""
    # Arrange
    scopes = {"project1": "admin", "project2": "user", "project3": "read"}
    token_data = TokenData(sub="user@example.com", scopes=scopes)

    with patch("app.database.authentication.register_connection") as mock_register:
        with patch("app.database.authentication.conf") as mock_conf:
            with patch("app.database.authentication.encode") as mock_encode:
                mock_register.return_value = True
                mock_conf.SECRET_KEY = "test_secret_key"
                mock_conf.ALGORITHM = "HS256"
                expected_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_multi.signature"
                mock_encode.return_value = expected_token

                # Act
                result = create_access_token(token_data)

                # Assert
                assert result == expected_token
                # Verify the token was created with correct data
                call_args = mock_encode.call_args
                assert call_args is not None
                token_dict = call_args[0][0]
                assert token_dict.get("sub") == "user@example.com"
                assert token_dict.get("scopes") == scopes


@pytest.mark.description("Test create_access_token encodes correct data structure")
@pytest.mark.tags("auth", "create_access_token", "mandatory")
@pytest.mark.test_steps(
    "Given valid TokenData",
    "When create_access_token is called",
    "Then the token data is correctly converted to dict format",
    "And encode receives the dict, secret key, and algorithm",
)
def test_create_access_token_encodes_correct_data() -> None:
    """Test that create_access_token properly encodes TokenData as dictionary."""
    # Arrange
    token_data = TokenData(sub="user@example.com", scopes={"*": "admin"})

    with patch("app.database.authentication.register_connection") as mock_register:
        with patch("app.database.authentication.conf") as mock_conf:
            with patch("app.database.authentication.encode") as mock_encode:
                mock_register.return_value = True
                mock_conf.SECRET_KEY = "secret_key_123"
                mock_conf.ALGORITHM = "HS256"
                mock_encode.return_value = "test_token"

                # Act
                create_access_token(token_data)

                # Assert
                mock_encode.assert_called_once_with(
                    {"sub": "user@example.com", "scopes": {"*": "admin"}},
                    "secret_key_123",
                    algorithm="HS256",
                )
