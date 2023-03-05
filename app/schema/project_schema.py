# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional

from pydantic import BaseModel

from app.schema.ticket_schema import TicketVersion


class Statistics(BaseModel):
    open: int
    cancelled: int
    blocked: int
    in_progress: int
    done: int

    def __getitem__(self, index):
        return self.dict().get(index, None)


class Project(BaseModel):
    name: str
    future: Optional[int]
    current: Optional[int]
    archived: Optional[int]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class TicketProject(BaseModel):
    name: str
    future: Optional[List[TicketVersion]]
    current: Optional[List[TicketVersion]]
    archived: Optional[List[TicketVersion]]

    def __getitem__(self, index):
        return self.dict().get(index, None)
        
        
class RegisterVersion(BaseModel):
    version: str

    def __getitem__(self, index):
        return self.dict().get(index, None)

class RegisterVersionResponse(BaseModel):
    inserted_id: int
    acknowledged: bool = True


class RegisterProject(BaseModel):
    name: str

    def __getitem__(self, index):
        return self.dict().get(index, None)


class ErrorMessage(BaseModel):
    detail: str

    def __getitem__(self, index):
        return self.dict().get(index, None)
