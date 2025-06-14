# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from app.schema.base_schema import ExtendedBaseModel


class TestFeature(ExtendedBaseModel):
    epic_name: str
    feature_name: str
    project_name: str
    description: str
    filename: str
    tags: str


class TestScenario(ExtendedBaseModel):
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
