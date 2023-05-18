# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum

from pydantic import BaseModel

"""
Enum for application error code
Class for application error management
"""


class ApplicationErrorCode(Enum):
    project_not_registered = 1
    version_not_found = 2
    campaign_not_found = 3
    occurrence_not_found = 4
    ticket_not_found = 5
    bug_not_found = 6
    epic_not_found = 7
    feature_not_found = 8
    scenario_not_found = 9

    duplicate_element = 100
    transition_forbidden = 101
    unknown_status = 102


class ApplicationError(BaseModel):
    error: ApplicationErrorCode
    message: str
