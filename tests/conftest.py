# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import importlib
import json
import os
import time
from typing import Any, Generator, List
from xml.etree import ElementTree

import psycopg
import pytest
from _pytest.config import Config, ExitCode, Parser
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from pytest import fixture
from starlette.responses import Response
from starlette.testclient import TestClient


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

        yield TestClient(app, raise_server_exceptions=False)
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


@fixture(scope="session")
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


def status_404_error_message_check(
    response: Response,
    expected_message: str,
) -> None:
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == expected_message


def pytest_addoption(parser: Parser) -> None:
    """Add CLI options for marker-to-property mapping."""
    group = parser.getgroup("metadata-plugin")
    group.addoption(
        "--metadata-mapping",
        action="store",
        metavar="MAPPING",
        default="description:description,path:path,tags:tags,testcase:testcase,test_steps:test_steps",
        help=(
            "Comma-separated list of marker:property mappings, e.g. "
            "'description:desc,path:reqPath,tags:labels,testcase:testKey'"
        ),
    )


from dotenv import load_dotenv


def pytest_configure(config: Config) -> None:
    load_dotenv("tests/.env")
    print("Setting environment data")
    os.environ["PG_DB"] = "test_db"

    """Register markers and parse mapping."""
    config.addinivalue_line("markers", "description(desc): add human-readable description")
    config.addinivalue_line("markers", "path(path): logical test path or requirement mapping")
    config.addinivalue_line("markers", "tags(*names): add one or more tags")
    config.addinivalue_line("markers", "testcase(id): external test case ID")
    config.addinivalue_line("markers", "test_steps(*names): add step")

    # Parse mapping string into dict
    mapping_str = config.getoption("--metadata-mapping")
    mapping = {}
    for entry in mapping_str.split(","):
        if ":" in entry:
            marker, prop = entry.split(":", 1)
            mapping[marker.strip()] = prop.strip()
    config._metadata_mapping = mapping


def _collect_metadata(item: Item, report: TestReport) -> dict:
    """Collect metadata based on configured mapping."""
    config = item.config
    metadata = {
        "name": item.name,
        "nodeid": item.nodeid,
        "outcome": report.outcome,
    }

    for marker_name, prop_name in config._metadata_mapping.items():
        marker = item.get_closest_marker(marker_name)
        if marker:
            if len(marker.args) == 1:
                metadata[prop_name] = marker.args[0]
            else:
                metadata[prop_name] = list(marker.args)

    return metadata


_OUTCOME_ORDER = {"failed": 2, "skipped": 1, "passed": 0}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo) -> None:
    outcome = yield
    report = outcome.get_result()

    metadata = _collect_metadata(item, report)

    # If this is the first phase, just store metadata
    if not hasattr(item, "test_metadata"):
        item.test_metadata = metadata
    else:
        # Merge outcomes: keep the "worst" one
        current = item.test_metadata["outcome"]
        if _OUTCOME_ORDER[metadata["outcome"]] > _OUTCOME_ORDER[current]:
            item.test_metadata["outcome"] = metadata["outcome"]

        # Also update duration if this phase has it
        if metadata.get("duration"):
            item.test_metadata["duration"] = metadata["duration"]


def pytest_sessionfinish(session: Session, exitstatus: ExitCode) -> None:
    """Export results to JSON at the end of session."""
    results = []
    for item in session.items:
        if hasattr(item, "test_metadata"):
            results.append(item.test_metadata)

    with open("pytest_metadata.json", "w") as f:
        json.dump(results, f, indent=2)


def pytest_runtest_logreport(report: TestReport) -> None:
    """Inject metadata into JUnit XML <properties>."""
    config = report.keywords
    if not hasattr(config, "_xml") or not hasattr(report, "test_metadata"):
        return

    xml = config._xml
    for suite in xml.node.findall("testsuite"):
        for case in suite.findall("testcase"):
            if case.attrib.get("name") == report.nodeid.split("::")[-1]:
                props = case.find("properties")
                if props is None:
                    props = ElementTree.SubElement(case, "properties")

                for key, value in report.test_metadata.items():
                    prop = ElementTree.SubElement(props, "property")
                    prop.set("name", key)
                    prop.set("value", str(value))
                return


# @pytest.hookimpl(optionalhook=True)
# def pytest_junitxml_add_properties(nodeid, report, properties):
#     """Inject our metadata into JUnit XML <properties>."""
#     if not hasattr(report, "test_metadata"):
#         return
#
#     md = report.test_metadata
#     for key, value in md.items():
#         if value is None:
#             continue
#         if isinstance(value, list):
#             for idx, step in enumerate(value, start=1):
#                 properties.append((f"{key}[{idx}]", str(step)))
#         else:
#             properties.append((key, str(value)))
