# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Optional

from pydantic import BaseModel

class Feature(BaseModel):
    name: str
    tags: Optional[str]
    filename: str

class Scenario(BaseModel):
    epic: str
    feature_name: str
    filename: str
    scenario_tech_id: int
    scenario_id: str
    name: str
    tags: str
    steps: str

class TestFeature(BaseModel):
    epic_name: str
    feature_name: str
    project_name: str
    description: str
    filename: str
    tags: str


class TestScenario(BaseModel):
    filename: str
    project_name: str
    scenario_id: str
    name: str
    is_outline: bool
    description: str
    steps: str
    tags: str
