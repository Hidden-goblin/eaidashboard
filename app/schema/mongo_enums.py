# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class BugStatusEnum(str, Enum):
    open = "open"
    closed = "closed"

    def __str__(self) -> str:
        return self.value


class BugCriticalityEnum(str, Enum):
    blocking = "blocking"
    major = "major"
    minor = "minor"

    def __str__(self) -> str:
        return self.value
