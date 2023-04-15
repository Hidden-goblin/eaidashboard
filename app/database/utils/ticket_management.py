# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import asyncio

from psycopg.rows import tuple_row

from app.app_exception import CampaignNotFound, NonUniqueError
from app.database.postgre.pg_campaigns_management import retrieve_campaign_id
from app.database.postgre.pg_tickets import get_ticket
from app.database.postgre.pg_versions import version_exists
from app.utils.pgdb import pool
from app.utils.project_alias import provide


async def add_ticket_to_campaign(project_name, version, occurrence, ticket_reference) -> int:
    """add a ticket to a campaign
    :return campaign_id"""
    async with asyncio.TaskGroup() as tg:
        ticket = tg.create_task(get_ticket(project_name, version, ticket_reference))
        campaign_id = tg.create_task(retrieve_campaign_id(project_name, version, occurrence))

    if ticket.result() is None:
        raise NonUniqueError(f"Found no ticket for project {project_name} in version {version} "
                             f"with reference {ticket_reference}.")
    if not bool(campaign_id.result()):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")

    with pool.connection() as connection:
        connection.row_factory = tuple_row

        result = connection.execute("insert into campaign_tickets"
                                    " (campaign_id, ticket_reference, ticket_id)"
                                    " select %s, %s, tk.id"
                                    " from tickets as tk"
                                    " join versions as ve on tk.current_version = ve.id"
                                    " join projects as pj on pj.id = ve.project_id"
                                    " where pj.alias = %s"
                                    " and ve.version = %s"
                                    " and tk.reference = %s"
                                    " on conflict (campaign_id, ticket_reference) do nothing;",
                                    (campaign_id.result()[0],
                                     ticket_reference,
                                     provide(project_name),
                                     version,
                                     ticket_reference))

        result = connection.execute("select id from campaign_tickets "
                                    "where campaign_id = %s "
                                    "and ticket_reference = %s;",
                                    (campaign_id.result()[0],
                                     ticket_reference)).fetchone()
        return result[0]

# flake8: noqa
async def move_ticket(project_name, version, current_ticket, target_version):  # noqa
    # Exist
    async with asyncio.TaskGroup() as tg:
        version_exist = tg.create_task(version_exists(project_name, version))
        target_version_exist = tg.create_task(version_exists(project_name,
                                                             target_version))
        ticket_in_campaign = tg.create_task()
    #


async def add_tickets_to_campaign(project_name, version, occurrence, ticket_references: dict):
    """Add tickets to campaign"""
    if not isinstance(ticket_references["ticket_references"], list):
        ticket_references["ticket_references"] = [ticket_references["ticket_references"]]
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for reference in ticket_references["ticket_references"]:
            tasks.append(tg.create_task(add_ticket_to_campaign(project_name,
                                                               version,
                                                               occurrence,
                                                               reference)))
    return [task.result() for task in tasks]
