# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.app_exception import IncorrectFieldsRequest

CAMPAIGN_TICKETS_FIELDS = [
    "reference",
    "summary",
    "epic_id",
    "feature_id",
    "scenario_id",
    "name",
    "steps",
    "status"
]


def validate_campaign_tickets_fields(fields):
    if any(field not in CAMPAIGN_TICKETS_FIELDS for field in fields):
        raise IncorrectFieldsRequest(f"Accepted fields are {''.join(CAMPAIGN_TICKETS_FIELDS)}. "
                                     f"Get {''.join(fields)}")
