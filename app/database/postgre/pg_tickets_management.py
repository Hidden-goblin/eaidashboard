# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from psycopg.rows import tuple_row

from app.database.mongo.tickets import get_tickets
from app.utils.pgdb import pool

async def get_campaign_ids_for_ticket(project_name, version, ticket_reference):
    pass

async def get_ticket_in_campaign(project_name, version, occurrence):
    """Retrieve all ticket reference from """
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute("select ct.ticket_reference "
                                    "from campaigns as cp "
                                    "inner join campaign_tickets as ct "
                                    " on ct.campaign_id = cp.id "
                                    "where cp.project_id = %s "
                                    "and cp.version = %s "
                                    "and cp.occurrence = %s;",
                                    (project_name, version, occurrence))
        return [row[0] for row in result.fetchall()]

async def get_tickets_not_in_campaign(project_name, version, occurrence):
    _tickets = await get_tickets(project_name, version)
    ticket_in_campaign = await get_ticket_in_campaign(project_name, version, occurrence)
    all_tickets = [ticket["reference"] for ticket in _tickets]

    return set(all_tickets).difference(ticket_in_campaign)
