# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import asyncio

from app.app_exception import CampaignNotFound, NonUniqueError
from app.database.mongo.tickets import get_ticket
from app.database.mongo.versions import get_version_and_collection
from app.database.postgre.pg_campaigns_management import retrieve_campaign_id
from app.utils.pgdb import pool


async def add_ticket_to_campaign(project_name, version, occurrence, ticket_reference) -> int:
    """add a ticket to a campaign
    :return campaign_ticket_id"""
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
        result = connection.execute("insert into campaign_tickets "
                                    "(campaign_id, ticket_reference) "
                                    "values (%s, %s) "
                                    "on conflict (campaign_id, ticket_reference) do nothing;",
                                    (campaign_id.result()[0], ticket.result()["reference"]))
        result = connection.execute("select id from campaign_tickets "
                                    "where campaign_id = %s "
                                    "and ticket_reference = %s;",
                                    (campaign_id.result()[0], ticket.result()["reference"])).fetchone()
        return result[0]

async def move_ticket(project_name, version, current_ticket, target_version):
    # Exist
    async with asyncio.TaskGroup() as tg:
        version_exist = tg.create_task(get_version_and_collection(project_name, version))
        target_version_exist = tg.create_task(get_version_and_collection(project_name,
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

