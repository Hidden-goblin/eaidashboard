# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from pydantic import BaseModel

from app.schema.error_code import ApplicationErrorCode


class PGResult(BaseModel):
    """
    Attributes
        - message: str
        - error: Optional[ApplicationErrorCode] = None
    """

    message: str
    error: Optional[ApplicationErrorCode] = None
