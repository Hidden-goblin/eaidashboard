# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class Repository(str, Enum):
    epics = "epics"
    features = "features"
    scenarios = "scenarios"


class CampaignStatus(str, Enum):
    recorded = "recorded"
    in_progress = "in progress"
    cancelled = "cancelled"
    done = "done"
    closed = "closed"
    paused = "paused"
