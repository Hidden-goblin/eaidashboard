# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pydantic import BaseModel


class UserModel(BaseModel):
    username: str
    password: str
    roles: dict


class ApiUserModel(UserModel):
    token: str = None
