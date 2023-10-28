# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schema.bugs_schema import Bugs
from app.schema.project_schema import Statistics
from app.schema.status_enum import StatusEnum


class Version(BaseModel):
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime] = None
    end_forecast: Optional[datetime] = None
    status: StatusEnum
    statistics: Statistics
    bugs: Bugs

    def __getitem__(self: "Version", index: str) -> str | datetime | StatusEnum | Statistics | Bugs:
        return self.model_dump().get(index, None)
