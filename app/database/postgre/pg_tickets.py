# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Union

from app.app_exception import VersionNotFound
from app.database.postgre.pg_versions import update_version_ticket_stats
from app.schema.project_schema import RegisterVersionResponse
from app.utils.pgdb import pool
from psycopg.rows import dict_row, tuple_row
from app.schema.ticket_schema import EnrichedTicket, Ticket, ToBeTicket, UpdatedTicket
from app.utils.project_alias import provide


async def add_ticket(project_name, project_version, ticket: ToBeTicket) -> RegisterVersionResponse:
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


async def get_ticket(project_name, project_version, reference) -> Ticket:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(
            "select tk.reference, tk.description, tk.status, tk.created, tk.updated"
            " from tickets as tk"
            " join versions as ve on ve.id = tk.current_version"
            " join projects as pj on pj.id = ve.project_id"
            " where pj.alias = %s"
            " and ve.version = %s"
            " and tk.reference = %s;",
            (provide(project_name), project_version, reference)
        ).fetchone()
        if row is None:
            raise VersionNotFound(f"Ticket {reference} does not exist in project {project_name}"
                                  f" version {project_version}")
        return Ticket(**row)


async def get_tickets(project_name, project_version) -> List[Ticket]:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        results = connection.execute("select tk.status,"
                                     " tk.reference,"
                                     " tk.description,"
                                     " tk.created,"
                                     " tk.updated"
                                     # " array_agg(cp.occurrence) as campaign_occurrences"
                                     " from tickets as tk"
                                     " join versions as ve on tk.current_version = ve.id"
                                    " join projects as pj on pj.id = ve.project_id"
                                    # " join campaign_tickets as cp_tk on cp_tk.ticket_id = tk.id"
                                    # " join campaigns as cp on cp.id = cp_tk.campaign_id"
                                    " where pj.alias = %s"
                                    " and ve.version = %s"
                                    # " group by tk.reference, tk.description, tk.status, tk.created,"
                                    # " tk.updated;"
                                     ,
                                    (provide(project_name), project_version))
        return [Ticket(**result) for result in results.fetchall()]


async def get_tickets_by_reference(project_name: str, project_version: str,
                                   references: Union[List, set]) -> List[Ticket]:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        _references = references if isinstance(references, list) else list(references)
        rows = connection.execute(
            "select tk.reference, tk.description, tk.status, tk.created, tk.updated"
            " from tickets as tk"
            " join versions as ve on ve.id = tk.current_version"
            " join projects as pj on pj.id = ve.project_id"
            " where pj.alias = %s"
            " and ve.version = %s"
            " and tk.reference = Any(%s);",
            (provide(project_name), project_version, _references)
        ).fetchall()
        return [Ticket(**row) for row in rows]

async def move_tickets(project_name,
                       version,
                       target_version: str,
                       tickets_reference: List[str] | str)->List[str]:
    current_version_id = None
    target_version_id = None
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        row_current_version = connection.execute(
            "select ve.id "
            " from versions as ve"
            " join projects as pj on pj.id = ve.project_id"
            " where pj.alias = %s"
            " and ve.version = %s;",
            (provide(project_name), version)
        ).fetchone()
        current_version_id = row_current_version[0]
        row_target_version = connection.execute(
            "select ve.id "
            " from versions as ve"
            " join projects as pj on pj.id = ve.project_id"
            " where pj.alias = %s"
            " and ve.version = %s;",
            (provide(project_name), target_version)
        ).fetchone()
        if row_target_version is None:
            raise VersionNotFound(f"The version {target_version} is not found.")
        target_version_id = row_target_version[0]
    _ticket_id = []

    with pool.connection() as connection:
        _ticket_references = tickets_reference if isinstance(tickets_reference, list) else [tickets_reference,]
        for _ticket in _ticket_references:
            connection.row_factory = tuple_row
            ticket_id = connection.execute(
                "select id"
                " from tickets"
                " where current_version = %s"
                " and reference = %s;",
                (current_version_id,
                 _ticket)
            ).fetchone()
            _ticket_id.append(ticket_id[0])
            connection.commit()
    return await _update_ticket_version(_ticket_id, target_version_id)


async def _update_ticket_version(ticket_ids, target_version_id) -> List[str]:
    _success = []
    _fail = []
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        for _id in ticket_ids:
            row = connection.execute(
                "update tickets"
                " set current_version = %s"
                " where id = %s;",
                (target_version_id,
                 _id)
            )
            if row is None:
                _fail.append(str(_id))
            else:
                _success.append(str(_id))
        if _fail:
            raise VersionNotFound(f"Cannot move '{', '.join(_fail)}' tickets")
        return _success


async def update_ticket(project_name: str,
                        project_version: str,
                        ticket_reference: str,
                        updated_ticket: UpdatedTicket) -> RegisterVersionResponse:
    # SPEC: update the version ticket count status where ticket status is updated
    if updated_ticket.status is not None:
        await update_version_ticket_stats(project_name,
                                          project_version,
                                          ticket_reference,
                                          updated_ticket.status)
    # SPEC: update the values first then move the ticket to another version
    query = ("update tickets tk"
             " set")
    update = [f" {key} = %s" for key, value in updated_ticket.dict().items() if
              value is not None and key != "version"]
    data = [value for key, value in updated_ticket.dict().items() if
            value is not None and key != "version"]
    data.extend([provide(project_name), project_version, ticket_reference])
    query = (f"{query} {', '.join(update)}"
             " from versions as ve"
             " join projects as pj on pj.id = ve.project_id"
             " where pj.alias = %s"
             " and ve.version = %s"
             " and ve.id = tk.current_version"
             " and tk.reference = %s"
             " returning tk.id, tk.reference, tk.description, tk.status, tk.created, tk.updated;")
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(query, data).fetchone()
        connection.commit()
        if row is None:
            raise VersionNotFound(
                f"Ticket {ticket_reference} does not exist in project {project_name}"
                f" version {project_version}")
        if updated_ticket.version is None:
            return RegisterVersionResponse(inserted_id = row["id"])

        result = await move_tickets(project_name,
                              project_version,
                              updated_ticket.version,
                              ticket_reference)
        return RegisterVersionResponse(inserted_id = ', '.join(result))

async def update_values(project_name, version):
    # Fake process
    # TODO: remove
    pass
