# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.app_exception import StatusTransitionForbidden, UnknownStatusException
from app.schema.project_schema import StatusEnum


def version_transition(current_status, to_be_status):
    if not StatusEnum.in_enum(to_be_status):
        raise UnknownStatusException("Status is not accepted")

    # Todo: set definition outside the function
    authorized_transition = {
        StatusEnum.RECORDED: [
            StatusEnum.TEST_PLAN_WRITING,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TEST_PLAN_WRITING: [
            StatusEnum.TEST_PLAN_SENT,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TEST_PLAN_SENT: [
            StatusEnum.TEST_PLAN_ACCEPTED,
            StatusEnum.CAMPAIGN_STARTED,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TEST_PLAN_ACCEPTED: [
            StatusEnum.CAMPAIGN_STARTED,
            StatusEnum.CANCELLED
        ],
        StatusEnum.CAMPAIGN_STARTED: [
            StatusEnum.CAMPAIGN_ENDED,
            StatusEnum.CANCELLED
        ],
        StatusEnum.CAMPAIGN_ENDED: [
            StatusEnum.TER_WRITING,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TER_WRITING: [
            StatusEnum.TER_SENT,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TER_SENT: [
            StatusEnum.ARCHIVED
        ],
        StatusEnum.CANCELLED: [
            StatusEnum.ARCHIVED,
            StatusEnum.RECORDED,
            StatusEnum.CAMPAIGN_STARTED,
            StatusEnum.CAMPAIGN_ENDED,
            StatusEnum.TEST_PLAN_WRITING,
            StatusEnum.TEST_PLAN_SENT,
            StatusEnum.TEST_PLAN_ACCEPTED,
            StatusEnum.TER_WRITING,
            StatusEnum.TER_SENT,
            StatusEnum.CANCELLED
        ]
    }
    if StatusEnum(to_be_status) not in authorized_transition[current_status]:
        raise StatusTransitionForbidden(f"You are not allowed to go from {current_status} to "
                                        f"{to_be_status} status.")
