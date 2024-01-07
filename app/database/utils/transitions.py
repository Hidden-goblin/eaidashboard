# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from app.app_exception import StatusTransitionForbidden, UnknownStatusException
from app.schema.status_enum import BugStatusEnum, DashTypeEnum, StatusEnum, TicketType

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

bug_authorized_transition = {
    BugStatusEnum.open: [BugStatusEnum.fix_ready,
                         BugStatusEnum.closed_not_a_defect],
    BugStatusEnum.fix_ready: [BugStatusEnum.closed,
                              BugStatusEnum.open],
    BugStatusEnum.closed: [BugStatusEnum.open],
    BugStatusEnum.closed_not_a_defect: [BugStatusEnum.open]
}


def version_transition(current_status: str,
                       to_be_status: str,
                       element_enum: DashTypeEnum = StatusEnum,
                       transition_dict: dict = None) -> None:
    """Raise an exception if the transition is not allowed

    Args:
        current_status (str):
        to_be_status (str):
        element_enum (DashTypeEnum): The transition enum type
        transition_dict (dict): The allowed transition schema
    Returns:
        None
    Raises:
        StatusTransitionForbidden exception
    """
    if not element_enum.in_enum(to_be_status):
        raise UnknownStatusException(f"Status '{to_be_status}' is not accepted")
    if transition_dict is None:
        transition_dict = authorized_transition
    # Todo: set definition outside the function

    _to_be_status = element_enum(to_be_status)
    _current_status = element_enum(current_status)
    _transition = transition_dict[_current_status]

    if (_current_status not in transition_dict
            or _to_be_status not in _transition) and _current_status != _to_be_status:
        raise StatusTransitionForbidden(f"You are not allowed to go from {current_status} to "
                                        f"{to_be_status} status.")
