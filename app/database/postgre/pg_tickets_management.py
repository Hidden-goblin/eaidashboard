# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Set

from psycopg.rows import tuple_row

from app.database.postgre.pg_tickets import get_tickets
from app.utils.pgdb import pool


async def get_ticket_in_campaign(
    project_name: str,
    version: str,
    occurrence: str,
) -> List[str]:
    """Retrieve all ticket reference from"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute(
            "select ct.ticket_reference "
            "from campaigns as cp "
            "inner join campaign_tickets as ct "
            " on ct.campaign_id = cp.id "
            "where cp.project_id = %s "
            "and cp.version = %s "
            "and cp.occurrence = %s;",
            (
                project_name,
                version,
                occurrence,
            ),
        )
        return [row[0] for row in result.fetchall()]


async def get_tickets_not_in_campaign(
    project_name: str,
    version: str,
    occurrence: str,
) -> Set[str]:
    _tickets = await get_tickets(
        project_name,
        version,
    )
    ticket_in_campaign = await get_ticket_in_campaign(
        project_name,
        version,
        occurrence,
    )
    all_tickets = [ticket["reference"] for ticket in _tickets]

    return set(all_tickets).difference(ticket_in_campaign)
