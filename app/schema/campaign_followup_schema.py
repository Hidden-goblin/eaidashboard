# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from pydantic import BaseModel

from app.schema.campaign_schema import Scenario
from app.schema.postgres_enums import CampaignStatusEnum


class ComputeResultSchema(BaseModel):
    """Attributes
    - result_uuid: str
    - campaign_id: int
    - scenarios: List[Scenario]
    """

    result_uuid: str
    campaign_id: int
    scenarios: List[Scenario]


class CampaignIdStatus(BaseModel):
    """Attributes
    - campaign_id: int
    - status: CampaignStatusEnum
    """

    campaign_id: int
    status: CampaignStatusEnum
