# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from app.schema.base_schema import ExtendedBaseModel
from app.schema.postgres_enums import CampaignStatusEnum
from app.schema.respository.scenario_schema import ScenarioExecution


class ComputeResultSchema(ExtendedBaseModel):
    """Attributes
    - result_uuid: str
    - campaign_id: int
    - scenarios: List[ScenarioExecution]
    """

    result_uuid: str
    campaign_id: int
    scenarios: List[ScenarioExecution]


class CampaignIdStatus(ExtendedBaseModel):
    """Attributes
    - campaign_id: int
    - status: CampaignStatusEnum
    """

    campaign_id: int
    status: CampaignStatusEnum
