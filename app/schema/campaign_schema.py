# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Union

from pydantic import BaseModel

from app.schema.postgres_enums import CampaignStatusEnum


class ToBeCampaign(BaseModel):
    version: str


class ScenarioCampaign(BaseModel):
    scenario_id: str
    epic: str
    feature_name: str
    feature_filename: Optional[str]


class TicketScenarioCampaign(BaseModel):
    ticket_reference: str
    scenarios: Union[ScenarioCampaign, List[ScenarioCampaign]]


class CampaignLight(BaseModel):
    project_name: str
    version: str
    occurrence: int
    description: Optional[str]
    status: CampaignStatusEnum
