# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schema.project_schema import TicketType


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

class EnrichedTicket(Ticket):
    campaign_occurrences: Optional[List[str]]


class UpdateTickets(BaseModel):
    open: Optional[int]
    cancelled: Optional[int]
    blocked: Optional[int]
    in_progress: Optional[int]
    done: Optional[int]
