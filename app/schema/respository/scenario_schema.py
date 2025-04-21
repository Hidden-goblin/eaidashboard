# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional

from pydantic import Field

from app.schema.base_schema import ExtendedBaseModel
from app.schema.postgres_enums import ScenarioStatusEnum, TestResultStatusEnum


class BaseScenario(ExtendedBaseModel):
    """
    Attributes:
        scenario_id: str
        epic: str
        feature_name: str
        filename: Optional str defaulted to None
    """

    scenario_id: str
    epic: str
    feature_name: str
    filename: Optional[str] = None


class ScenarioExecution(BaseScenario):
    """
    Attributes:
        scenario_id: str
        epic: str
        feature_name: str
        filename: Optional str defaulted to None
        name: str
        steps: str
        status: ScenarioStatusEnum | TestResultStatusEnum
        scenario_tech_id: Optional int defaulted as None
    """

    name: str
    steps: str
    status: ScenarioStatusEnum | TestResultStatusEnum
    scenario_tech_id: int = Field(default=None)


class Scenario(BaseScenario):
    scenario_tech_id: int
    name: str
    tags: str
    steps: str
    is_deleted: Optional[bool] = False
    is_outline: Optional[bool] = False

    # @staticmethod
    # async def from_base_scenario(project_name: str, scenario: BaseScenario) -> "Scenario":
    #     _scenario = await db_get_scenario_from_partial(
    #         project_name,
    #         scenario.epic,
    #         scenario.feature_name,
    #         scenario.scenario_id,
    #         scenario.filename,
    #     )
    #     return Scenario(**_scenario)


class Scenarios(ExtendedBaseModel):
    scenarios: List[Scenario]

    def __len__(self: "Scenarios") -> int:
        return len(self.scenarios)

    def scenario_tech_ids(self: "Scenarios") -> list[int]:
        """Extract tech ids from scenarios"""
        return [scn.scenario_tech_id for scn in self.scenarios]

    def scenario_not_in_scenarios(self: "Scenarios", scenario_id: List[str]) -> set[str]:
        return set(scenario_id) - {scenario.scenario_id for scenario in self.scenarios}
