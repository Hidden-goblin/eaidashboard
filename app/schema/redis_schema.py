# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime

from pydantic import BaseModel


class RdTestResult(BaseModel):
    campaign_id: int
    version: str
    is_partial: bool
    status: str
    created: datetime = datetime.now()
    updated: datetime = datetime.now()
    message: str = ""
