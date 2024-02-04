# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
from datetime import datetime
from typing import List, Optional

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

    def __getitem__(self: "Bugs", index: str) -> None | int:
        return self.model_dump().get(index, None)


class BugsStatistics(BaseModel):
    open_blocking: int = 0
    open_major: int = 0
    open_minor: int = 0
    closed_blocking: int = 0
    closed_major: int = 0
    closed_minor: int = 0

    def __getitem__(self: "BugsStatistics", index: str) -> None | int:
        return self.model_dump().get(index, None)


class CampaignTicketScenario(BaseModel, extra='forbid'):
    ticket_reference: str = Field(min_length=1)
    scenario_tech_id: int
    occurrence: int

    # def to_api(self: "CampaignTicketScenario") -> str:
    #     return f"/{self.occurrence}/tickets/{self.ticket_reference}/scenarios/{self.scenario_tech_id}"


class BugTicket(BaseModel, extra='forbid'):
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str
    created: datetime = datetime.now()
    updated: datetime = datetime.now()
    url: Optional[str] = ""
    status: BugStatusEnum = BugStatusEnum.open
    criticality: BugCriticalityEnum = BugCriticalityEnum.major
    related_to: Optional[List[CampaignTicketScenario | str | int | None | dict] | str ] = []

    def __getitem__(self: "BugTicket",
                    index: str) -> None | str | datetime | BugStatusEnum | BugCriticalityEnum | List:
        return self.model_dump().get(index, None)

    def serialize(self: "BugTicket") -> None:
        if self.related_to and isinstance(self.related_to, list):
            self.related_to = [CampaignTicketScenario(**json.loads(item)) for item in self.related_to]
        elif self.related_to and isinstance(self.related_to, str):
            self.related_to = [CampaignTicketScenario(**json.loads(self.related_to))]


class BugTicketFull(BugTicket):
    internal_id: int

    # def to_api(self: "BugTicketFull"):
    #     return {**self.model_dump(),
    #             "related_to": [f"/campaign/{self.version}/{item.to_api()}" for item in self.related_to]}


class UpdateBugTicket(BaseModel, extra='forbid'):
    title: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    updated: datetime = datetime.now()
    url: Optional[str] = None
    status: Optional[BugStatusEnum] = None
    criticality: Optional[BugCriticalityEnum] = None
    related_to: Optional[List[CampaignTicketScenario | str | int | None | dict] | str] = []
    unlink_scenario: Optional[List[CampaignTicketScenario | str | int | None | dict]| str] = []

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

    def serialize(self: "UpdateBugTicket") -> None:
        if self.related_to:
            if isinstance(self.related_to, str):
                self.related_to = [CampaignTicketScenario(**json.loads(self.related_to))]
            else:
                self.related_to = [CampaignTicketScenario(**json.loads(item)) for item in self.related_to]
        if self.unlink_scenario:
            if isinstance(self.unlink_scenario, str):
                self.unlink_scenario = [CampaignTicketScenario(**json.loads(self.unlink_scenario))]
            else:
                self.unlink_scenario = [CampaignTicketScenario(**json.loads(item)) for item in self.unlink_scenario]



class UpdateVersion(BaseModel):
    started: Optional[str] = None
    end_forecast: Optional[str] = None
    status: Optional[str] = None

    def __getitem__(self: "UpdateVersion", index: str) -> None | str:
        return self.model_dump().get(index, None)
