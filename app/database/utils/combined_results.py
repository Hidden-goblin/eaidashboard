# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.database.mongo.tickets import get_ticket
from app.database.postgre.testcampaign import db_get_campaign_ticket_scenarios
from app.schema.campaign_schema import TicketScenario


async def get_ticket_with_scenarios(project_name, version, occurrence, ticket_reference):
    ticket = await get_ticket(project_name, version, ticket_reference)
    scenarios = await db_get_campaign_ticket_scenarios(project_name,
                                                       version,
                                                       occurrence,
                                                       ticket_reference)
    return TicketScenario(reference=ticket_reference,
                          summary=ticket["description"],
                          status=ticket["status"],
                          scenarios=scenarios)
