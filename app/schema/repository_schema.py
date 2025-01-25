# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional

from pydantic import BaseModel


class Feature(BaseModel):
    name: str
    tags: Optional[str]
    filename: str

    def __getitem__(self: "Feature", index: str) -> str | None:
        return self.model_dump().get(index, None)

class BaseScenario(BaseModel):
    epic: str
    feature_name: str
    filename: Optional[str] = None
    scenario_id: str

    def __getitem__(self: "BaseScenario", index: str) -> str | None:
        return self.model_dump().get(index, None)

class Scenario(BaseScenario):
    scenario_tech_id: int
    name: str
    tags: str
    steps: str
    is_deleted: Optional[bool] = False

    def __getitem__(self: "Scenario", index: str) -> str | int | None:
        return self.model_dump().get(index, None)


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
