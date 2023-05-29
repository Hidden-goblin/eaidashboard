# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class DashTypeEnum(Enum):
    def __str__(self) -> str:
        return self.value

    @classmethod
    def in_enum(cls, item):
        return item in [str(val) for val in cls.__members__.values()]

    @classmethod
    def list(cls):
        return [str(val) for val in cls.__members__.values()]


class TicketType(DashTypeEnum):
    OPEN = "open"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class StatusEnum(DashTypeEnum):
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
