# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

from starlette.testclient import TestClient


# noinspection PyUnresolvedReferences
class TestMonitoring:
    def test_health_indicators(
        self: "TestMonitoring",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get("/health")

        assert response.status_code == 200, response.text
        indicators = [
            "app_status",
            "container_status",
            "cpu",
            "os",
            "memory",
            "pg_in_recovery",
            "pg_connections",
            "redis_ping",
        ]
        assert all(ind in response.json().keys() for ind in indicators), response.text
        assert all(ind in indicators for ind in response.json().keys()), response.text

    def test_metrics(
        self: "TestMonitoring",
        application: Generator[TestClient, Any, None],
    ) -> None:
        response = application.get("/metrics")
        assert response.status_code == 200, response.text
