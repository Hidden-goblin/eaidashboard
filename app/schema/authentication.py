# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from pydantic import BaseModel


class TokenData(BaseModel):
    email: str
    scopes: List[str] = []
