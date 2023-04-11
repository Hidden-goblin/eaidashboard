# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from enum import Enum

from app.app_exception import StatusTransitionForbidden, UnknownStatusException
from app.schema.status_enum import DashTypeEnum, StatusEnum, TicketType

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

ticket_authorized_transition = {
    TicketType.OPEN: [TicketType.CANCELLED,
                      TicketType.IN_PROGRESS],
    TicketType.IN_PROGRESS: [TicketType.CANCELLED,
                             TicketType.BLOCKED,
                             TicketType.DONE],
    TicketType.BLOCKED: [TicketType.IN_PROGRESS,
                         TicketType.CANCELLED],
    TicketType.CANCELLED: [TicketType.OPEN,
                           TicketType.IN_PROGRESS]
}

def version_transition(current_status,
                       to_be_status,
                       element_enum: DashTypeEnum = StatusEnum,
                       transition_dict: dict = None):
    """Raise an exception if the transition is not allowed"""
    if not element_enum.in_enum(to_be_status):
        raise UnknownStatusException("Status is not accepted")
    if transition_dict is None:
        transition_dict = authorized_transition
    # Todo: set definition outside the function

    _to_be_status = element_enum(to_be_status)
    _current_status = element_enum(current_status)
    _transition = transition_dict[_current_status]
    if (_current_status not in transition_dict
            or _to_be_status not in _transition):
        raise StatusTransitionForbidden(f"You are not allowed to go from {current_status} to "
                                        f"{to_be_status} status.")
