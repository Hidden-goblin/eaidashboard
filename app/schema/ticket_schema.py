# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Extra, root_validator

from app.schema.status_enum import TicketType


class Ticket(BaseModel):
    status: str
    reference: str
    description: str
    created: datetime
    updated: datetime

    def __getitem__(self, index):
        return self.dict().get(index, None)


class ToBeTicket(BaseModel):
    reference: str
    description: str
    status: str = TicketType.OPEN.value
    created: datetime = datetime.now()
    updated: datetime = datetime.now()

    def __getitem__(self, index):
        return self.dict().get(index, None)


class UpdatedTicket(BaseModel, extra=Extra.forbid):
    description: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    updated: datetime = datetime.now()

    def __getitem__(self, index):
        return self.dict().get(index, None)

    @root_validator
    def check_at_least_one(cls, values):
        keys = ("description", "status", "version")
        if all(values.get(key) is None for key in keys):
            raise ValueError(f"UpdatedTicket must have at least one key of '{keys}'")
        return values

class EnrichedTicket(Ticket):
    campaign_occurrences: Optional[List[str]]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class UpdateTickets(BaseModel):
    open: Optional[int]
    cancelled: Optional[int]
    blocked: Optional[int]
    in_progress: Optional[int]
    done: Optional[int]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class TicketVersion(BaseModel):
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime]
    end_forecast: Optional[datetime]
    status: str

    def __getitem__(self, index):
        return self.dict().get(index, None)
