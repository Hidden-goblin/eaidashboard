# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Union

from pydantic import BaseModel, model_validator

from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum, TestResultStatusEnum
from app.schema.repository_schema import BaseScenario
from app.schema.status_enum import TicketType
from app.schema.ticket_schema import Ticket


class ToBeCampaign(BaseModel, extra="forbid"):
    """
    Attributes
         - version: str
    """

    version: str

    def __getitem__(
        self: "ToBeCampaign",
        index: str,
    ) -> str | None:
        return self.model_dump().get(index, None)


class Scenarios(BaseModel):
    """
    Attributes
        - epic: str
        - feature_name: str
        - scenarios_ids: List[str]
    """

    epic: str
    feature_name: str
    scenario_ids: List[str]

    def __getitem__(
        self: "Scenarios",
        index: str,
    ) -> str | List[str] | None:
        return self.model_dump().get(index, None)


class TicketScenarioCampaign(BaseModel):
    """
    Attributes
        - ticket_reference: str
        - scenarios: Optional[Union[ScenarioCampaign, List[ScenarioCampaign]]]
    """

    ticket_reference: str
    scenarios: Optional[Union[BaseScenario, List[BaseScenario]]] = None

    def __getitem__(
        self: "TicketScenarioCampaign",
        index: str,
    ) -> str | BaseScenario | List[BaseScenario] | None:
        return self.model_dump().get(index, None)


class CampaignLight(BaseModel):
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

    def __getitem__(
        self: "CampaignLight",
        index: str,
    ) -> str | int | CampaignStatusEnum | None:
        return self.model_dump().get(index, None)


class Scenario(BaseModel):
    """
    Attributes
        - epic_id: str
        - feature_id: str
        - scenario_id: str
        - name: str
        - steps: str
        - status: ScenarioStatusEnum | TestResultStatusEnum
    """

    # TODO: Fix serialized warning
    epic_id: str
    feature_id: str
    scenario_id: str
    name: str
    steps: str
    status: ScenarioStatusEnum | TestResultStatusEnum

    def __getitem__(
        self: "Scenario",
        index: str,
    ) -> str | ScenarioStatusEnum | TestResultStatusEnum | None:
        return self.model_dump().get(index, None)

    def get(
        self: "Scenario",
        index: str,
        default: str | ScenarioStatusEnum | TestResultStatusEnum,
    ) -> str | ScenarioStatusEnum | TestResultStatusEnum:
        return self.model_dump().get(index, default)


class ScenarioInternal(Scenario):
    """
    Attributes
        - epic_id: str
        - feature_id: str
        - scenario_id: str
        - internal_id: str
        - name: str
        - steps: str
        - status: ScenarioStatusEnum | TestResultStatusEnum
    """

    internal_id: int


class TicketScenario(BaseModel):
    """
    Attributes
        - reference: str
        - summary: str
        - status: Optional[TicketType] = TicketType.OPEN
        - scenarios: Optional[list[Union[Scenario, ScenarioInternal]]] = []
    """

    reference: str
    summary: str
    status: Optional[TicketType] = TicketType.OPEN
    scenarios: Optional[list[Union[Scenario, ScenarioInternal]]] = []

    def __getitem__(
        self: "TicketScenario",
        index: str,
    ) -> str | TicketType | List[Scenario | ScenarioInternal] | None:
        return self.model_dump().get(index, None)


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


class CampaignPatch(BaseModel):
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


class FillCampaignResult(BaseModel):
    """
    Attributes:
        - campaign_ticket_id: str | int
        - errors: List
    """

    campaign_ticket_id: str | int
    errors: List = []
