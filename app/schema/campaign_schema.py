# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Union

from pydantic import model_validator

from app.schema.base_schema import ExtendedBaseModel
from app.schema.postgres_enums import CampaignStatusEnum
from app.schema.respository.scenario_schema import BaseScenario, ScenarioExecution
from app.schema.status_enum import TicketType
from app.schema.ticket_schema import Ticket


class ToBeCampaign(ExtendedBaseModel, extra="forbid"):
    """
    Attributes
         - version: str
    """

    version: str


class TicketScenarioCampaign(ExtendedBaseModel):
    """
    Attributes
        - ticket_reference: str
        - scenarios: Optional[Union[ScenarioCampaign, List[ScenarioCampaign]]]
    """

    ticket_reference: str
    scenarios: Optional[Union[BaseScenario, List[BaseScenario]]] = None


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


class TicketScenario(ExtendedBaseModel):
    """
    Attributes
        - reference: str
        - summary: str
        - status: Optional[TicketType] = TicketType.OPEN
        - scenarios: Optional[list[ScenarioExecution]] = []
    """

    reference: str
    summary: str
    status: Optional[TicketType] = TicketType.OPEN
    scenarios: Optional[list[ScenarioExecution]] = []


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


class CampaignPatch(ExtendedBaseModel):
    """
    Attributes
        - status: CampaignStatusEnum
        - description: Optional[str]
    """

    status: Optional[CampaignStatusEnum] = None
    description: Optional[str] = None

    @model_validator(mode="before")
    def check_at_least_one(cls: "CampaignPatch", ticket: "CampaignPatch"):  # noqa: ANN101, ANN201
        keys = ("description", "status")
        if all(ticket.get(key) is None for key in keys):
            raise ValueError(f"CampaignPatch must have at least one key of '{keys}'")
        return ticket


class FillCampaignResult(ExtendedBaseModel):
    """
    Attributes:
        - campaign_ticket_id: str | int
        - errors: List
    """

    campaign_ticket_id: str | int
    errors: List = []
