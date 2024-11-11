# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum

from pydantic import BaseModel

"""
Enum for application error code
Class for application error management
"""


class ApplicationErrorCode(Enum):
    # 404 error
    project_not_registered = 1
    version_not_found = 2
    campaign_not_found = 3
    occurrence_not_found = 4
    ticket_not_found = 5
    bug_not_found = 6
    epic_not_found = 7
    feature_not_found = 8
    scenario_not_found = 9
    user_not_found = 10
    # 409 error
    duplicate_element = 100
    # 400 error
    transition_forbidden = 101
    unknown_status = 102
    type_error = 103
    value_error = 104
    # 500 error
    database_error = 200
    database_no_update = 201


class ApplicationError(BaseModel):
    """
    Attributes:
     - error: ApplicationErrorCode
     - message: str
    """

    error: ApplicationErrorCode
    message: str


class ErrorMessage(BaseModel):
    detail: str

    def __getitem__(self: "ErrorMessage", index: str) -> str:
        return self.model_dump().get(index, None)
