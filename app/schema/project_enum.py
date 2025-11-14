# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum, StrEnum


class DashCollection(Enum):
    """The enum for the various project states"""

    CURRENT = "current"
    FUTURE = "future"
    ARCHIVED = "archived"


class ProjectProjections(StrEnum):
    """The enum for the various projections"""

    VERSIONS = "versions"
    CAMPAIGNS = "campaigns"
    FUTURE_VERSIONS = "future_versions"
    ARCHIVED_VERSIONS = "archived_versions"
    ARCHIVED_CAMPAIGNS = "archived_campaigns"
