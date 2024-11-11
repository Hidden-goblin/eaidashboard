# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import asyncio

from app.database.postgre.pg_tickets import get_ticket
from app.database.postgre.testcampaign import db_get_campaign_ticket_scenarios
from app.schema.campaign_schema import TicketScenario
from app.schema.error_code import ApplicationError


async def get_ticket_with_scenarios(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
) -> TicketScenario | ApplicationError:
    async with asyncio.TaskGroup() as tg:
        ticket = tg.create_task(
            get_ticket(
                project_name,
                version,
                ticket_reference,
            )
        )
        scenarios = tg.create_task(
            db_get_campaign_ticket_scenarios(
                project_name,
                version,
                occurrence,
                ticket_reference,
            )
        )
    if isinstance(ticket.result(), ApplicationError):
        return ticket.result()
    if isinstance(scenarios.result(), ApplicationError):
        return scenarios.result()
    return TicketScenario(
        reference=ticket_reference,
        summary=ticket.result()["description"],
        status=ticket.result()["status"],
        scenarios=scenarios.result(),
    )
