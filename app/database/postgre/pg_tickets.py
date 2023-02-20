# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.utils.pgdb import pool
from psycopg.rows import dict_row
from app.schema.ticket_schema import ToBeTicket

async def add_ticket(project_name, project_version, ticket: ToBeTicket):
    pass


async def get_ticket(project_name, project_version, reference):
    pass

async def get_tickets(project_name, project_version) -> List[Ticket]:
    pass 

async def get_tickets_by_reference(project_name: str, project_version: str, references: Union[List, set]):
    pass


async def move_tickets(project_name, version, ticket_type, ticket_dispatch):
    pass


async def update_ticket(project_name: str,
                  project_version: str,
                  ticket_reference: str,
                  updated_ticket: UpdatedTicket):
    pass




