# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from pydantic import BaseModel, Field


class ExtendedBaseModel(BaseModel):
    def __getitem__(
        self: "ExtendedBaseModel",
        index: str,
    ) -> Any | None:  # noqa: ANN401
        return self.model_dump().get(index, None)

    def get(
        self: "ExtendedBaseModel",
        index: str,
        default: Any = None,  # noqa: ANN401
    ) -> Any | None:  # noqa: ANN401
        return self.model_dump().get(index, default)


class CreateUpdateModel(ExtendedBaseModel):
    resource_id: str | int
    message: str
    acknowledged: bool = Field(default=True)
    raw_data: dict | None = Field(default=None)

    def __add__(self: "CreateUpdateModel", other: "CreateUpdateModel") -> "CreateUpdateModel":
        if not isinstance(other, CreateUpdateModel):
            return other
        raw_data = {}
        # Merge raw_data
        if self.raw_data is None and other.raw_data is None:
            pass
        elif self.raw_data is not None and other.raw_data is not None:
            raw_data = self.raw_data | other.raw_data
        elif self.raw_data is not None and other.raw_data is None:
            raw_data = self.raw_data
        else:
            raw_data = other.raw_data

        if str(self.resource_id).casefold() != str(other.resource_id).casefold():
            resource_id = self.resource_id
            raw_data["collision"] = raw_data.get("collision", [])
            raw_data["collision"].append({"resource_id": other.resource_id, "message": other.message})
        else:
            resource_id = self.resource_id

        return CreateUpdateModel(
            resource_id=resource_id,
            message=f"{self.message}\n{other.message}",
            acknowledged=self.acknowledged or other.acknowledged,
            raw_data=raw_data if raw_data else None,
        )
