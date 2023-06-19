# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from pydantic import BaseModel


class TokenData(BaseModel):
    sub: str
    scopes: dict = {"*": None}

    def to_dict(self: "TokenData") -> dict:
        return {"sub": self.sub,
                "scopes": self.scopes}


class Scopes(BaseModel):
    scopes: dict = {"*": None}

    def right(self: "Scopes", project_name: str) -> str:
        if self.scopes.get("*") == "admin":
            return "admin"
        else:
            return self.scopes.get(project_name)
