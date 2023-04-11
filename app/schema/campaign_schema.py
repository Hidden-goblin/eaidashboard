# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Union
from dataclasses import dataclass

from pydantic import BaseModel

from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum, TestResultStatusEnum
from app.schema.status_enum import TicketType


class ToBeCampaign(BaseModel):
    version: str

    def __getitem__(self, index):
        return self.dict().get(index, None)


class ScenarioCampaign(BaseModel):
    scenario_id: str
    epic: str
    feature_name: str
    feature_filename: Optional[str]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class Scenarios(BaseModel):
    epic: str
    feature_name: str
    scenario_ids: List[str]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class TicketScenarioCampaign(BaseModel):
    ticket_reference: str
    scenarios: Optional[Union[ScenarioCampaign, List[ScenarioCampaign]]]

    def __getitem__(self, index):
        return self.dict().get(index, None)


class CampaignLight(BaseModel):
    project_name: str
    version: str
    occurrence: int
    description: Optional[str]
    status: CampaignStatusEnum

    def __getitem__(self, index):
        return self.dict().get(index, None)


class Scenario(BaseModel):
    epic_id: str
    feature_id: str
    scenario_id: str
    name: str
    steps: str
    status: ScenarioStatusEnum | TestResultStatusEnum

    def __getitem__(self, index):
        return self.dict().get(index, None)

    def get(self, index, default):
        return self.dict().get(index, default)

class ScenarioInternal(Scenario):
    internal_id: int

class TicketScenario(BaseModel):
    reference: str
    summary: str
    status: Optional[TicketType] = TicketType.OPEN
    scenarios: Optional[list[Union[Scenario, ScenarioInternal]]] = []
    def __getitem__(self, index):
        return self.dict().get(index, None)

class CampaignFull(CampaignLight):
    tickets: Optional[list[TicketScenario]] = []


class CampaignPatch(BaseModel):
    status: TicketType