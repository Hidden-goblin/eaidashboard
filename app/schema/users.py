# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional

from pydantic import BaseModel


class UpdateMe(BaseModel):
    password: str
    new_password: str

    def __getitem__(self: "UpdateMe", index: str) -> str:
        return self.dict().get(index, None)


class UpdateUser(BaseModel):
    username: str
    password: Optional[str]
    scopes: Optional[List[str]]

    def __getitem__(self: "UpdateUser", index: str) -> str | List[str]:
        return self.dict().get(index, None)
