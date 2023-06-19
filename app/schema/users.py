# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from pydantic import BaseModel


class UpdateMe(BaseModel):
    password: str
    new_password: str

    def __getitem__(self: "UpdateMe", index: str) -> str:
        return self.dict().get(index, None)


class UpdateUser(BaseModel):
    username: str
    password: Optional[str]
    scopes: Optional[dict]

    def __getitem__(self: "UpdateUser", index: str) -> str | dict:
        return self.dict().get(index, None)

class User(BaseModel):
    username: str
    scopes: dict
    password: Optional[str]

    def __getitem__(self: "User", index: str) -> str | dict:
        return self.dict().get(index, None)

    def right(self: "User", project_name: str) -> str:
        if self.scopes.get("*") == "admin":
            return "admin"
        else:
            return self.scopes.get(project_name)

