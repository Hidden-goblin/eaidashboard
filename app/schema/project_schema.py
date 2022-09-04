# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class StatusEnum(Enum):
    IN_PROGRESS = "in progress"
    RECORDED = "recorded"
    CAMPAIGN_STARTED = "campaign started"
    CAMPAIGN_ENDED = "campaign ended"
    TEST_PLAN_WRITING = "test plan writing"
    TEST_PLAN_SENT = "test plan sent"
    TEST_PLAN_ACCEPTED = "test plan accepted"
    TER_WRITING = "ter writing"
    TER_SENT = "ter sent"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

    def __str__(self):
        return self.value


class TicketType(Enum):
    OPEN = "open"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    def __str__(self):
        return self.value


class Statistics(BaseModel):
    open: int
    cancelled: int
    blocked: int
    in_progress: int
    done: int


class Ticket(BaseModel):
    status: str
    reference: str
    description: str
    created: datetime
    updated: datetime


class ToBeTicket(BaseModel):
    reference: str
    description: str
    status: str = TicketType.OPEN.value
    created: datetime = datetime.now()
    updated: datetime = datetime.now()


class UpdatedTicket(BaseModel):
    description: Optional[str]
    status: Optional[str]
    version: Optional[str]
    updated: datetime = datetime.now()


class UpdateTickets(BaseModel):
    open: Optional[int]
    cancelled: Optional[int]
    blocked: Optional[int]
    in_progress: Optional[int]
    done: Optional[int]


class Bugs(BaseModel):
    open_blocking: Optional[int]
    open_major: Optional[int]
    open_minor: Optional[int]
    closed_blocking: Optional[int]
    closed_major: Optional[int]
    closed_minor: Optional[int]


class BugTicket(BaseModel):
    version: str
    title: str
    description: str
    created: datetime = datetime.now()
    updated: datetime = datetime.now()
    url: str
    status: str


class UpdateBugTicket(BaseModel):
    version: str
    title: Optional[str]
    description: Optional[str]
    updated: datetime = datetime.now()
    url: Optional[str]
    status: Optional[str]


class Version(BaseModel):
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime]
    end_forecast: Optional[datetime]
    status: str
    statistics: Statistics
    bugs: Bugs


class UpdateVersion(BaseModel):
    started: Optional[str]
    end_forecast: Optional[str]
    status: Optional[str]


class TicketVersion(BaseModel):
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime]
    end_forecast: Optional[datetime]
    status: str
        

class Project(BaseModel):
    name: str
    future: Optional[int]
    current: Optional[int]
    archived: Optional[int]


class TicketProject(BaseModel):
    name: str
    future: Optional[List[TicketVersion]]
    current: Optional[List[TicketVersion]]
    archived: Optional[List[TicketVersion]]
        
        
class RegisterVersion(BaseModel):
    version: str


class RegisterProject(BaseModel):
    name: str


class ErrorMessage(BaseModel):
    detail: str


class TestFeature(BaseModel):
    epic_name: str
    feature_name: str
    project_name: str
    description: str
    filename: str
    tags: str


class TestScenario(BaseModel):
    filename: str
    project_name: str
    scenario_id: str
    name: str
    is_outline: bool
    description: str
    steps: str
    tags: str
