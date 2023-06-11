# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class BugCriticalityEnum(str, Enum):
    blocking = "blocking"
    major = "major"
    minor = "minor"

    def __str__(self: "BugCriticalityEnum") -> str:
        return self.value
