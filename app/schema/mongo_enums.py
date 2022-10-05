# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class BugStatusEnum(str, Enum):
    open = "open"
    closed = "closed"


class BugCriticalityEnum(str, Enum):
    blocking = "blocking"
    major = "major"
    minor = "minor"
