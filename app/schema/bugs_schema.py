# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.status_enum import BugStatusEnum


class Bugs(BaseModel):
    open_blocking: Optional[int] = 0
    open_major: Optional[int] = 0
    open_minor: Optional[int] = 0
    closed_blocking: Optional[int] = 0
    closed_major: Optional[int] = 0
    closed_minor: Optional[int] = 0

    def __getitem__(self: "Bugs", index: str) -> int:
        return self.model_dump().get(index, None)


class BugsStatistics(BaseModel):
    open_blocking: int = 0
    open_major: int = 0
    open_minor: int = 0
    closed_blocking: int = 0
    closed_major: int = 0
    closed_minor: int = 0

    def __getitem__(self: "BugsStatistics", index: str) -> int:
        return self.model_dump().get(index, None)


class BugTicket(BaseModel, extra='forbid'):
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str
    created: datetime = datetime.now()
    updated: datetime = datetime.now()
    url: Optional[str] = ""
    status: BugStatusEnum = BugStatusEnum.open
    criticality: BugCriticalityEnum = BugCriticalityEnum.major

    def __getitem__(self: "BugTicket",
                    index: str) -> str | datetime | BugStatusEnum | BugCriticalityEnum:
        return self.model_dump().get(index, None)


class BugTicketFull(BugTicket):
    internal_id: int


class UpdateBugTicket(BaseModel, extra='forbid'):
    title: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    updated: datetime = datetime.now()
    url: Optional[str] = None
    status: Optional[BugStatusEnum] = None
    criticality: Optional[BugCriticalityEnum] = None

    def to_dict(self: "UpdateBugTicket") -> dict:
        temp = {"title": self.title,
                "description": self.description,
                "updated": self.updated,
                "url": self.url,
                "status": self.status,
                "criticality": self.criticality,
                "version": self.version}
        return {key: value for key, value in temp.items() if value is not None}

    def to_sql(self: "UpdateBugTicket") -> dict:
        temp = self.to_dict()
        if "status" in temp:
            temp["status"] = temp["status"].value
        return temp


class UpdateVersion(BaseModel):
    started: Optional[str] = None
    end_forecast: Optional[str] = None
    status: Optional[str] = None

    def __getitem__(self: "UpdateVersion", index: str) -> str:
        return self.model_dump().get(index, None)
