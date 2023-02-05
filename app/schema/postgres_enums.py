# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum


class RepositoryEnum(str, Enum):
    epics = "epics"
    features = "features"
    scenarios = "scenarios"


class CampaignStatusEnum(str, Enum):
    recorded = "recorded"
    in_progress = "in progress"
    cancelled = "cancelled"
    done = "done"
    closed = "closed"
    paused = "paused"


class ScenarioStatusEnum(str, Enum):
    recorded = "recorded"
    in_progress = "in progress"
    cancelled = "cancelled"
    done = "done"
    waiting_fix = "waiting fix"
    waiting_answer = "waiting answer"


class CampaignTicketTableEnum(str, Enum):
    reference = "reference"
    status = "status"
    epic_id = "epic_id"
    feature_id = "feature_id"
    name = "name"
    steps = "steps"
    summary = "summary"
    scenario_id = "scenario_id"


class TestResultStatusEnum(str, Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
