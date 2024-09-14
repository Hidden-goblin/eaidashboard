import pytest

from app.database.utils.transitions import ticket_authorized_transition, version_transition
from app.schema.status_enum import TicketType


class TestTransition:
    testdata = [
        ("open", "in_progress"),
        ("open", "cancelled"),
        ("in_progress", "cancelled"),
        ("in_progress", "blocked"),
        ("in_progress", "done"),
        ("cancelled", "open"),
        ("cancelled", "in_progress"),
        ("blocked", "cancelled"),
        ("blocked", "in_progress"),
    ]

    @pytest.mark.parametrize("from_status,to_status", testdata)
    def test_ticket(self: "TestTransition", from_status: str, to_status: str) -> None:
        version_transition(from_status, to_status, TicketType, ticket_authorized_transition)
