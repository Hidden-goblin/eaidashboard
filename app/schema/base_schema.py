# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from pydantic import BaseModel


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
