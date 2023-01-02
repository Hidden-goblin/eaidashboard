# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class DashCollection(Enum):
    TICKETS = "tickets"
    ARCHIVED = "archived"
    CURRENT = "current"
    FUTURE = "future"
    BUGS = "bugs"
    RESULTS = "results"

    def __str__(self):
        return self.value
