# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any, List

from pydantic import AliasChoices, Field, field_validator

from app.database.postgre.test_repository.scenarios_utils import db_get_scenarios
from app.schema.base_schema import ExtendedBaseModel
from app.schema.respository.scenario_schema import Scenarios


class Feature(ExtendedBaseModel):
    """
    Attributes:
        name (name | feature_name): str
        tags: str = ""
        filename: str = None
        description: str = ""
        epic_name (epic |epic_name) = ""
        project_name: str = ""
        scenarios: Scenarios |None= None
        scenario_ids: list[str|int] |str = []

    """

    name: str = Field(validation_alias=AliasChoices("name", "feature_name"))
    tags: str = Field(default="")
    filename: str = Field(default=None)
    description: str = Field(default="")
    epic_name: str = Field(validation_alias=AliasChoices("epic_name", "epic"), default="")
    project_name: str = Field(default="")
    scenarios: Scenarios | None = None
    scenario_ids: list[str | int] | str = []

    @classmethod
    @field_validator("scenario_ids", mode="before")
    def validate_scenario_ids(cls: "Feature", value: Any) -> List[str | int]:  # noqa: ANN401
        if isinstance(value, (str, int)):
            return [value]
        elif isinstance(value, list):
            return value
        else:
            raise ValueError("scenario_ids must be a string, integer, or list of strings/integers")

    async def gather_scenarios_from_ids(self: "Feature", remove_deleted: bool = True) -> None:
        """Fill the self.scenarios with Scenarios object based on the self.scenario_ids"""
        self.scenarios = await db_get_scenarios(
            project_name=self.project_name,
            epic_name=self.epic_name,
            feature_name=self.name,
            scenarios_ref=self.scenario_ids,
            feature_filename=self.filename,
            remove_deleted=remove_deleted,
        )

    def deleted_scenarios(self: "Feature") -> set[str]:
        return self.scenarios.scenario_not_in_scenarios(self.scenario_ids)

    def scenario_tech_ids(self: "Feature") -> list[int]:
        """Extract tech ids from scenarios"""
        return self.scenarios.scenario_tech_ids()
