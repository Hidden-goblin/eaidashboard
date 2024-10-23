# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.schema.status_enum import TicketType


class Ticket(BaseModel):
    status: str
    reference: str
    description: str
    created: datetime
    updated: datetime

    def __getitem__(self: "Ticket", index: str) -> str | datetime | None:
        return self.model_dump().get(index, None)


class ToBeTicket(BaseModel):
    reference: str = Field(min_length=1)
    description: str
    status: str = TicketType.OPEN.value
    created: datetime = datetime.now()
    updated: datetime = datetime.now()

    def __getitem__(self: "ToBeTicket", index: str) -> str | datetime | None:
        return self.model_dump().get(index, None)


class UpdatedTicket(BaseModel, extra="forbid"):
    description: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    updated: datetime = datetime.now()

    def __getitem__(self: "UpdatedTicket", index: str) -> str | datetime | None:
        return self.model_dump().get(index, None)

    @model_validator(mode="before")
    def check_at_least_one(cls, ticket: "UpdatedTicket"):  # noqa: ANN101, ANN201
        keys = ("description", "status", "version")
        if all(ticket.get(key) is None for key in keys):
            raise ValueError(f"UpdatedTicket must have at least one key of '{keys}'")
        return ticket


class EnrichedTicket(Ticket):
    campaign_occurrences: Optional[List[str] | List[int]]

    def __getitem__(self: "EnrichedTicket", index: str) -> List[str] | None:
        return self.model_dump().get(index, None)


class UpdateTickets(BaseModel):
    open: Optional[int]
    cancelled: Optional[int]
    blocked: Optional[int]
    in_progress: Optional[int]
    done: Optional[int]

    def __getitem__(self: "UpdateTickets", index: str) -> int | None:
        return self.model_dump().get(index, None)


class TicketVersion(BaseModel):
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime]
    end_forecast: Optional[datetime]
    status: str

    def __getitem__(self: "TicketVersion", index: str) -> str | datetime | None:
        return self.model_dump().get(index, None)
