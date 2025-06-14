# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, Union

from pydantic import model_validator

from app.schema.base_schema import ExtendedBaseModel
from app.schema.postgres_enums import CampaignStatusEnum
from app.schema.respository.feature_schema import Feature
from app.schema.respository.scenario_schema import BaseScenario, ScenarioExecution
from app.schema.status_enum import TicketType


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

    def to_features(self: "TicketScenarioCampaign", project_name: str) -> List[Feature]:
        """
        Convert the scenarios into Features
        Args:
            project_name: str

        Returns:List of Feature object

        """
        if self.scenarios is None:
            return []
        # Need the project_name (/)
        # Don't create multiple time the same object
        if isinstance(self.scenarios, BaseScenario):
            return [
                Feature(
                    name=self.scenarios.feature_name,
                    epic_name=self.scenarios.epic,
                    project_name=project_name,
                    scenario_ids=[self.scenarios.scenario_id],
                )
            ]
        else:
            accumulator = {}
            for scenario in self.scenarios:
                key = (scenario.epic, scenario.feature_name)
                if key in accumulator:
                    accumulator[key].scenario_ids.append(scenario.scenario_id)
                else:
                    accumulator[key] = Feature(
                        name=scenario.feature_name,
                        epic_name=scenario.epic,
                        project_name=project_name,
                        scenario_ids=[scenario.scenario_id],
                    )
            return list(accumulator.values())


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
