
import importlib
import os
from typing import Any, Generator, List

import pytest
from pytest import fixture
from starlette.testclient import TestClient

from tests.populate import populate_db


def pytest_configure(config) -> None:
    """Set up the environment variables for the tests."""
    os.environ["PG_URL"] = "localhost"
    os.environ["PG_PORT"] = "5432"
    os.environ["PG_DB"] = "test_db"
    os.environ["PG_USR"] = "test"
    os.environ["PG_PWD"] = "test"
    os.environ["REDIS_URL"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"


@fixture(autouse=True, scope="function")
def application(postgresql, redisdb) -> Generator[TestClient, Any, None]:
    """Session-wide test `Application` fixture."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PG_URL", str(postgresql.info.host))
        mp.setenv("PG_PORT", str(postgresql.info.port))
        mp.setenv("PG_DB", str(postgresql.info.dbname))
        mp.setenv("PG_USR", str(postgresql.info.user))
        mp.setenv("PG_PWD", str(postgresql.info.password))
        mp.setenv("REDIS_URL", str(redisdb.connection_pool.connection_kwargs["host"]))
        mp.setenv("REDIS_PORT", str(redisdb.connection_pool.connection_kwargs["port"]))

        import app.conf
        import app.utils.pgdb
        import app.utils.redis

        importlib.reload(app.conf)
        importlib.reload(app.utils.pgdb)
        importlib.reload(app.utils.redis)

        populate_db(postgresql)

        from app.api import app

        yield TestClient(app)


@fixture(scope="function")
def logged(application: TestClient) -> Generator[dict[str, str], Any, None]:
    response = application.post(
        "/api/v1/token",
        data={"username": "admin@admin.fr", "password": "admin"},
    )
    token = response.json()["access_token"]
    yield {"Authorization": f"Bearer {token}"}
    application.delete(
        "/api/v1/token",
        headers={"Authorization": f"Bearer {token}"},
    )


def error_message_extraction(error_messages: List[dict] | dict) -> List[dict] | dict:
    switch = False
    if isinstance(error_messages, dict):
        switch = True
        error_messages = [error_messages]
    _result = []
    for error_message in error_messages:
        if "url" in error_message:
            error_message.pop("url")
        if "ctx" in error_message:
            error_message.pop("ctx")
        if "input" in error_message:
            error_message.pop("input")
        _result.append(error_message)
    return _result[0] if switch else _result
