# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class DashCollection(Enum):
    ARCHIVED = "archived"
    CURRENT = "current"
    FUTURE = "future"

    def __str__(self):
        return self.value