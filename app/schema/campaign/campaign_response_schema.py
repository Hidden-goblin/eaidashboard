# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from app.schema.base_schema import ExtendedBaseModel
from app.schema.campaign_schema import TicketScenario
from app.schema.postgres_enums import CampaignStatusEnum
from app.schema.ticket_schema import Ticket


class CampaignLight(ExtendedBaseModel):
    """
    Attributes
        - project_name: str
        - version: str
        - occurrence: int
        - description: Optional[str]
        - status: CampaignStatusEnum
    """

    project_name: str
    version: str
    occurrence: int
    description: Optional[str] = ""
    status: CampaignStatusEnum


class CampaignFull(CampaignLight):
    """
    Attributes
        - project_name: str
        - version: str
        - occurrence: int
        - description: Optional[str]
        - status: CampaignStatusEnum
        - tickets: Optional[list[TicketScenario | Ticket]] = []
    """

    tickets: Optional[list[TicketScenario | Ticket]] = []
