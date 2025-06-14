# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from pydantic import AliasChoices, Field

from app.schema.base_schema import ExtendedBaseModel
from app.schema.respository.feature_schema import Feature


class Epic(ExtendedBaseModel):
    epic_name: str = Field(validation_alias=AliasChoices("epic_name", "epic"))
    project_name: str
    epic_tech_id: int
    features: List[Feature] = Field(default=[])


class Epics(ExtendedBaseModel):
    epics: List[Epic]
