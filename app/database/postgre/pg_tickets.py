# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Union

from app.schema.project_schema import RegisterVersionResponse
from app.utils.pgdb import pool
from psycopg.rows import dict_row, tuple_row
from app.schema.ticket_schema import EnrichedTicket, Ticket, ToBeTicket, UpdatedTicket
from app.utils.project_alias import provide


async def add_ticket(project_name, project_version, ticket: ToBeTicket):
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        row = connection.execute(
            "insert into tickets (reference, description, status, current_version, project_id)"
            " select %s, %s, %s, ve.id, pj.id"
            " from projects as pj "
            " join versions as ve on ve.project_id = pj.id"
            " where ve.version = %s and pj.alias = %s"
            " returning id;",
            (ticket.reference,
             ticket.description,
             ticket.status,
             project_version,
             provide(project_name))).fetchone()
        return RegisterVersionResponse(inserted_id=row[0])

async def get_ticket(project_name, project_version, reference):
    pass

async def get_tickets(project_name, project_version) -> List[Ticket]:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        results = connection.execute("select tk.status,"
                                    " tk.reference,"
                                    " tk.description,"
                                    " tk.created,"
                                    " tk.updated,"
                                    " array_agg(cp.occurrence) as campaign_occurrences"
                                    " from tickets as tk"
                                    " join versions as ve on tk.current_version = ve.id"
                                    " join projects as pj on pj.id = ve.project_id"
                                    " join campaign_tickets as cp_tk on cp_tk.ticket_id = tk.id"
                                    " join campaigns as cp on cp.id = cp_tk.campaign_id"
                                    " where pj.alias = %s"
                                    " and ve.version = %s"
                                    " group by tk.reference, tk.description, tk.status, tk.created,"
                                    " tk.updated;",
                                    (provide(project_name), project_version))
        return [EnrichedTicket(**result) for result in results.fetchall()]

async def get_tickets_by_reference(project_name: str, project_version: str, references: Union[List, set]):
    pass


async def move_tickets(project_name, version, ticket_type, ticket_dispatch):
    pass


async def update_ticket(project_name: str,
                  project_version: str,
                  ticket_reference: str,
                  updated_ticket: UpdatedTicket):
    pass

async def update_values(project_name, version):
    # Fake process
    # TODO: remove
    pass



