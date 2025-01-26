# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional, override

from pydantic import BaseModel

from app.database.postgre.test_repository.scenarios_utils import db_get_scenario_from_partial


class Epic(BaseModel):
    epic_name: str
    project_name: str
    epic_tech_id: int

    def __getitem__(self: "Epic", index: str) -> str | int | None:
        return self.model_dump().get(index, None)

class Feature(BaseModel):
    name: str
    tags: Optional[str]
    filename: str

    def __getitem__(self: "Feature", index: str) -> str | None:
        return self.model_dump().get(index, None)


class BaseScenario(BaseModel):
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

    def __getitem__(self: "BaseScenario", index: str) -> str | None:
        return self.model_dump().get(index, None)


class Scenario(BaseScenario):
    scenario_tech_id: int
    name: str
    tags: str
    steps: str
    is_deleted: Optional[bool] = False
    is_outline: Optional[bool] = False

    @override
    def __getitem__(self: "Scenario", index: str) -> str | int | None:
        return self.model_dump().get(index, None)

    @staticmethod
    async def from_base_scenario(project_name: str, scenario: BaseScenario) -> "Scenario":
        _scenario = await db_get_scenario_from_partial(
            project_name,
            scenario.epic,
            scenario.feature_name,
            scenario.scenario_id,
            scenario.filename,
        )
        return Scenario(**_scenario)


class Scenarios(BaseModel):
    scenarios: List[Scenario]

    def scenario_tech_ids(self: "Scenarios") -> List[int]:
        """Extract tech ids from scenarios"""
        return [scn.scenario_tech_id for scn in self.scenarios]


class TestFeature(BaseModel):
    epic_name: str
    feature_name: str
    project_name: str
    description: str
    filename: str
    tags: str

    def __getitem__(self: "TestFeature", index: str) -> str | None:
        return self.model_dump().get(index, None)


class TestScenario(BaseModel):
    filename: str
    project_name: str
    scenario_id: str
    name: str
    is_outline: bool
    description: str
    steps: str
    tags: str
    is_deleted: Optional[bool] = False
    scenario_tech_id: Optional[int] = -1

    def __getitem__(self: "TestScenario", index: str) -> str | bool | None:
        return self.model_dump().get(index, None)
