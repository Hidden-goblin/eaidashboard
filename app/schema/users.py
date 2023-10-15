# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
from typing import Optional

from pydantic import BaseModel, model_validator


class UpdateMe(BaseModel):
    password: str
    new_password: str

    def __getitem__(self: "UpdateMe", index: str) -> str:
        return self.model_dump().get(index, None)


class UpdateUser(BaseModel, extra='forbid'):
    username: str
    password: Optional[str] = None
    scopes: Optional[dict] = {}

    def __getitem__(self: "UpdateUser", index: str) -> str | dict:
        return self.model_dump().get(index, None)

    @model_validator(mode='before')
    def check_at_least_one(cls, values: dict) -> dict:  # noqa: ANN101
        keys = ("password", "scopes")
        if all(values.get(key) is None for key in keys):
            raise ValueError(f"UpdateUser must have at least one key of '{keys}'")
        return values


class User(BaseModel):
    username: str
    scopes: str | dict
    password: Optional[str] = None

    def __init__(self: "User", username: str, scopes: str | dict, password: str = None) -> None:
        super().__init__(username=username, scopes=scopes, password=password)
        if isinstance(self.scopes, str):
            self.scopes = json.loads(scopes)

    def __getitem__(self: "User", index: str) -> str | dict:
        return self.model_dump().get(index, None)

    def right(self: "User", project_name: str) -> str:
        if self.scopes.get("*") == "admin":
            return "admin"
        else:
            return self.scopes.get(project_name)


class UserLight(BaseModel):
    username: str
    scopes: dict | str

    def __init__(self: "User", username: str, scopes: str | dict) -> None:
        super().__init__(username=username, scopes=scopes)
        if isinstance(self.scopes, str):
            self.scopes = json.loads(scopes)

    def __getitem__(self: "User", index: str) -> str | dict:
        return self.model_dump().get(index, None)

    def right(self: "User", project_name: str) -> str:
        if self.scopes.get("*") == "admin":
            return "admin"
        else:
            return self.scopes.get(project_name)
