# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import importlib
import os
import time
from typing import Any, Generator, List

import psycopg
import pytest
from pytest import fixture
from starlette.testclient import TestClient


def pytest_configure(config) -> None:  # noqa: ANN001
    os.environ["PG_DB"] = "test_db"


def pytest_unconfigure(config) -> None:  # noqa: ANN001
    os.environ.pop("PG_DB")


@fixture(autouse=True, scope="session")
def application() -> Generator[TestClient, Any, None]:
    # Override the environment variable
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PG_DB", "test_db")
        import app.conf
        import app.utils.pgdb

        importlib.reload(app.conf)
        importlib.reload(app.utils.pgdb)
        from app.conf import postgre_setting_string, postgre_string

        assert "test_db" in postgre_string, postgre_string
        print(postgre_string)
        # Import your FastAPI application
        from app.api import app

        yield TestClient(app)
        # teardown_stuff
        from app.utils.pgdb import pool

        pool.close()
        del pool
        time.sleep(6.0)
        conn = psycopg.connect(
            postgre_setting_string,
            autocommit=True,
        )
        cur = conn.cursor()
        cur.execute("""SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = 'test_db';""")
        cur.execute("DROP DATABASE IF EXISTS test_db")


@fixture(scope="function")
def logged(application: Generator[TestClient, Any, None]) -> Generator[dict[str, str], Any, None]:
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
