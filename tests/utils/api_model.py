# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, Generator

from starlette.testclient import TestClient


# noinspection PyUnresolvedReferences
def log_in(
    user: dict,
    application: Generator[TestClient, Any, None],
) -> dict:
    """Log in the application"""
    response = application.post("/api/v1/token", data={"username": user["username"], "password": user["password"]})
    if response.status_code != 200:
        raise Exception(response.text)

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# noinspection PyUnresolvedReferences
def log_out(
    header: dict,
    application: Generator[TestClient, Any, None],
) -> None:
    """Log out from app"""
    response = application.delete("/api/v1/token", headers=header)
    if response.status_code != 204:
        raise Exception(response.text)
