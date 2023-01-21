# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class RestTestResultHeaderEnum(str, Enum):
    JSON = "application/json"
    HTML = "text/html"
    CSV = "text/csv"


class RestTestResultCategoryEnum(str, Enum):
    EPICS = "epics"
    FEATURES = "features"
    SCENARIOS = "scenarios"

class RestTestResultRenderingEnum(str, Enum):
    STACKED = "stacked"
    MAP = "map"