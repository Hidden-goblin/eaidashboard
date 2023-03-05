# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schema.bugs_schema import Bugs
from app.schema.project_schema import Statistics


class Version(BaseModel):
    version: str
    created: datetime
    updated: datetime
    started: Optional[datetime]
    end_forecast: Optional[datetime]
    status: str
    statistics: Statistics
    bugs: Bugs

    def __getitem__(self, index):
        return self.dict().get(index, None)
