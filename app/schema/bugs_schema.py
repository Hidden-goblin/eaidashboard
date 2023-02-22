# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.py_objectid import PyObjectId


class Bugs(BaseModel):
    open_blocking: Optional[int]
    open_major: Optional[int]
    open_minor: Optional[int]
    closed_blocking: Optional[int]
    closed_major: Optional[int]
    closed_minor: Optional[int]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class BugsStatistics(BaseModel):
    open_blocking: int = 0
    open_major: int = 0
    open_minor: int = 0
    closed_blocking: int = 0
    closed_major: int = 0
    closed_minor: int = 0

    def __getitem__(self, index):
        return self.dict().get(index, None)


class BugTicket(BaseModel):
    version: str
    title: str
    description: str
    created: datetime = datetime.now()
    updated: datetime = datetime.now()
    url: str
    status: BugStatusEnum
    criticality: BugCriticalityEnum

    def __getitem__(self, index):
        return self.dict().get(index, None)


class BugTicketResponse(BaseModel):
    internal_id: PyObjectId = Field(default_factory=PyObjectId)
    version: str
    title: str
    description: str
    created: datetime
    updated: datetime
    url: str
    status: BugStatusEnum
    criticality: BugCriticalityEnum

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        # schema_extra = {
        #     "example": {
        #         "name": "Jane Doe",
        #         "email": "jdoe@example.com",
        #         "course": "Experiments, Science, and Fashion in Nanophotonics",
        #         "gpa": "3.0",
        #     }
        # }


class UpdateBugTicket(BaseModel):
    title: Optional[str]
    version: Optional[str]
    description: Optional[str]
    updated: datetime = datetime.now()
    url: Optional[str]
    status: Optional[BugStatusEnum]
    criticality: Optional[BugCriticalityEnum]

    def to_dict(self):
        temp = {"title": self.title,
                "description": self.description,
                "updated": self.updated,
                "url": self.url,
                "status": self.status,
                "criticality": self.criticality,
                "version": self.version}
        return {key: value for key, value in temp.items() if value is not None}


class UpdateVersion(BaseModel):
    started: Optional[str]
    end_forecast: Optional[str]
    status: Optional[str]

    def __getitem__(self, index):
        return self.dict().get(index, None)
