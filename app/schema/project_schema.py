# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schema.bugs_schema import BugsStatistics
from app.schema.status_enum import StatusEnum
from app.schema.ticket_schema import TicketVersion


class Statistics(BaseModel):
    open: int
    cancelled: int
    blocked: int
    in_progress: int
    done: int

    def __getitem__(self: "Statistics", index: str) -> int:
        return self.model_dump().get(index, None)


class Project(BaseModel):
    name: str
    future: Optional[int] = 0
    current: Optional[int] = 0
    archived: Optional[int] = 0

    def __getitem__(self: "Project", index: str) -> str | int:
        return self.model_dump().get(index, None)


class Dashboard(BaseModel):
    name: str
    alias: str
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime] = None
    end_forecast: Optional[datetime] = None
    status: StatusEnum
    statistics: Statistics
    bugs: BugsStatistics


class TicketProject(BaseModel):
    name: str
    future: Optional[List[TicketVersion]] = None
    current: Optional[List[TicketVersion]] = None
    archived: Optional[List[TicketVersion]] = None

    def __getitem__(self: "TicketProject", index: str) -> str | List[TicketVersion]:
        return self.model_dump().get(index, None)


class RegisterVersion(BaseModel):
    version: str

    def __getitem__(self: "RegisterVersion", index: str) -> str:
        return self.model_dump().get(index, None)


class RegisterVersionResponse(BaseModel):
    """Attributes:
        inserted_id (str)
        acknowledged (bool)
    """
    inserted_id: str | int
    acknowledged: bool = True
    message: Optional[str] = None


class RegisterProject(BaseModel):
    name: str

    def __getitem__(self: "RegisterProject", index: str) -> str:
        return self.model_dump().get(index, None)
