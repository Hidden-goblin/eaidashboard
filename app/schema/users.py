# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional

from pydantic import BaseModel


class UpdateMe(BaseModel):
    password: str
    new_password: str


class UpdateUser(BaseModel):
    username: str
    password: Optional[str]
    scopes: Optional[List[str]]
