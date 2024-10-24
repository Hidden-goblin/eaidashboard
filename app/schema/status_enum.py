# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum
from typing import List


class DashTypeEnum(Enum):
    def __str__(self: "DashTypeEnum") -> str:
        return self.value

    @classmethod
    def in_enum(cls: "DashTypeEnum", item: str) -> bool:
        return item in [str(val) for val in cls.__members__.values()]

    @classmethod
    def list(cls: "DashTypeEnum") -> List[str]:
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


class BugStatusEnum(DashTypeEnum):
    open = "open"
    closed = "closed"
    closed_not_a_defect = "closed not a defect"
    fix_ready = "fix ready"
