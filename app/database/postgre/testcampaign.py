# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from psycopg.rows import dict_row, tuple_row

from app.app_exception import CampaignNotFound, ScenarioNotFound, TicketNotFound

from app.database.postgre.pg_campaigns_management import is_campaign_exist, retrieve_campaign_id
from app.database.postgre.testrepository import db_get_scenarios_id
from app.database.postgre.pg_tickets import (get_ticket,
                                             get_tickets_by_reference)
from app.database.redis.rs_file_management import rs_invalidate_file

from app.database.utils.ticket_management import add_ticket_to_campaign
from app.database.utils.transitions import ticket_authorized_transition, version_transition
from app.schema.postgres_enums import (CampaignStatusEnum, ScenarioStatusEnum)
from app.schema.campaign_schema import (CampaignFull,
                                        CampaignPatch, Scenario,
                                        ScenarioCampaign,
                                        ScenarioInternal,
                                        Scenarios,
                                        TicketScenario,
                                        TicketScenarioCampaign)
from app.schema.status_enum import TicketType
from app.utils.pgdb import pool
from app.utils.project_alias import provide


async def fill_campaign(project_name: str,
                        version: str,
                        occurrence: str,
                        content: TicketScenarioCampaign):
    """Attach ticket to campaign
    Attach scenarios to campaign"""
    campaign_ticket_id = await add_ticket_to_campaign(project_name,
                                                version,
                                                occurrence,
                                                content.ticket_reference)
    if isinstance(content.scenarios, list):
        scenarios = content.scenarios
    elif isinstance(content.scenarios, ScenarioCampaign):
        scenarios = [content.scenarios]
    else:
        return

    errors = []
    with pool.connection() as connection:
        for scenario in scenarios:
            # Retrieve scenario_internal_id id
            scenario_id = await db_get_scenarios_id(project_name,
                                              scenario.epic,
                                              scenario.feature_name,
                                              scenario.scenario_id,
                                              scenario.feature_filename)

            if not scenario_id or len(scenario_id) > 1:
                errors.append(f"Found {len(scenario_id)} scenarios while expecting one and"
                              f" only one.\n"
                              f"Search criteria was {scenario}")
                break

            result = connection.execute("insert into campaign_ticket_scenarios "
                                        "(campaign_id, scenario_id,status) "
                                        "values (%s, %s, %s) "
                                        "on conflict (campaign_id, scenario_id) "
                                        "do nothing;",
                                        (campaign_ticket_id, scenario_id[0],
                                         CampaignStatusEnum.recorded))

        # I must do something with it


async def retrieve_campaign_ticket_id(project_name: str,
                                version: str,
                                occurrence: str,
                                ticket_reference: str):
    if not await is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = await retrieve_campaign_id(project_name, version, occurrence)

    ticket = await get_ticket(project_name, version, ticket_reference)
    if not ticket:
        raise TicketNotFound(f"Ticket {ticket_reference} does not belong to project {project_name},"
                             f" version {version}")

    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute("select id "
                                  "from campaign_tickets "
                                  "where campaign_id = %s "
                                  "and ticket_reference = %s;",
                                  (campaign_id[0], ticket_reference)).fetchone()


async def get_campaign_content(project_name: str,
                               version: str,
                               occurrence: str,
                               only_status: bool = False):
    """Retrieve the campaign fully (tickets and scenarios). No pagination."""
    if not await is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    # Unique id for project/version/occurrence triplet
    campaign_id = await retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
        connection.row_factory = dict_row

        # Prepare the result
        camp = CampaignFull(project_name=project_name,
                            version= version,
                            occurrence=int(occurrence),
                            status=campaign_id[1])
        if only_status:
            return camp
        # Select all sql data related to the campaign
        result = connection.execute("select ct.ticket_reference as reference, "
                                    "ct.id as campaign_id "
                                    "from campaign_tickets as ct "
                                    "where ct.campaign_id = %s "
                                    "order by ct.ticket_reference desc;",
                                    (campaign_id[0],))
        # Accumulators
        tickets = set()
        current_ticket = None
        # Iter over result and dispatch between new ticket and ticket's scenario_internal_id
        for row in result.fetchall():
            if row["reference"] not in tickets:
                if current_ticket:
                    camp.tickets.append(current_ticket)
                tickets.add(row['reference'])
                current_ticket = TicketScenario(reference=row['reference'],
                                                summary="",
                                                scenarios= await db_get_campaign_ticket_scenarios(
                                                    project_name,
                                                    version,
                                                    occurrence,
                                                    row['reference']))
        # Add the last ticket
        if current_ticket is not None:
            camp.tickets.append(current_ticket)

        # Retrieve data from mongo
        tickets_data = {tick["reference"]: tick["description"]
                        for tick in await get_tickets_by_reference(project_name, version, tickets)}

        # Update the tickets with their summary
        for tick in camp.tickets:
            if tick and tickets_data[tick["reference"]]:
                tick.summary = tickets_data[tick["reference"]]
        return camp


def db_get_campaign_scenarios(campaign_id: int) -> List[Scenario]:
    """:return list of dict epic_id, feature_id, scenario_id, name, steps and status"""

    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute("select ep.name as epic_id,"
                                    " ft.name as feature_id,"
                                    " sc.scenario_id as scenario_id,"
                                    " sc.name as name,"
                                    " sc.steps as steps,"
                                    " cts.status as status"
                                    " from campaign_ticket_scenarios as cts"
                                    " join scenarios as sc on sc.id = cts.scenario_id"
                                    " join features as ft on sc.feature_id = ft.id"
                                    " join epics as ep on ft.epic_id = ep.id"
                                    " join campaign_tickets as ct on ct.id = cts.campaign_ticket_id"
                                    " where ct.campaign_id = %s;", (campaign_id,))
        return [Scenario(**item) for item in result.fetchall()]


async def db_get_campaign_tickets(project_name,
                            version,
                            occurrence):
    """"""
    if not await is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = await retrieve_campaign_id(project_name, version, occurrence)

    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute("select distinct ticket_reference "
                                    "from campaign_tickets as ct "
                                    "where campaign_id = %s "
                                    "order by ct.ticket_reference desc;",
                                    (campaign_id[0],))
        tickets = result.fetchall()
        updated_tickets = list(await get_tickets_by_reference(project_name,
                                                        version,
                                                        [ticket[0] for ticket in tickets]))

        return {"project": project_name,
                "version": version,
                "occurrence": occurrence,
                "status": campaign_id[1],
                "tickets": updated_tickets}


async def db_get_campaign_ticket_scenarios(project_name: str,
                                     version: str,
                                     occurrence: str,
                                     reference: str):
    """Retrieve scenarios associated to a ticket in a campaign"""
    if not await is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = await retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute("select sc.scenario_id as scenario_id,"
                                    " sc.name as name,"
                                    " sc.steps as steps,"
                                    " cts.status as status,"
                                    " ft.name as feature_id,"
                                    " sc.id as internal_id,"
                                    " ep.name as epic_id"
                                    " from campaign_tickets as ct"
                                    " join campaign_ticket_scenarios as cts"
                                    " on ct.id = cts.campaign_ticket_id"
                                    " join scenarios as sc on sc.id = cts.scenario_id"
                                    " join features as ft on sc.feature_id = ft.id"
                                    " join epics as ep on ft.epic_id = ep.id"
                                    " where ct.campaign_id = %s"
                                    " and ct.ticket_reference = %s;",
                                    (campaign_id[0], reference))
        return [ScenarioInternal(**res) for res in result.fetchall()]


async def db_get_campaign_ticket_scenario(project_name,
                                    version,
                                    occurrence,
                                    reference,
                                    scenario_id):
    if not await is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_ticket_id = await retrieve_campaign_ticket_id(project_name, version, occurrence, reference)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute("select sc.scenario_id as scenario_id,"
                                    " sc.name as name,"
                                    " sc.steps as steps,"
                                    " cts.status as status"
                                    " from campaign_ticket_scenarios as cts"
                                    " join scenarios as sc on sc.id = cts.scenario_id"
                                    " where cts.campaign_ticket_id = %s"
                                    " and sc.scenario_id = %s;",
                                    (campaign_ticket_id[0], scenario_id))
        return result.fetchone()


async def db_put_campaign_ticket_scenarios(project_name,
                                     version,
                                     occurrence,
                                     reference,
                                     scenarios: List[Scenarios]
                                     ):
    campaign_ticket_id = await retrieve_campaign_ticket_id(project_name,
                                                     version,
                                                     occurrence,
                                                     reference)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        # Get scenario_internal_id ids
        scenarios_id = []
        for scenario in scenarios:
            scenarios_id.extend(await db_get_scenarios_id(project_name,
                                                    scenario.epic,
                                                    scenario.feature_name,
                                                    scenario.scenario_ids))
        connection.execute("insert into campaign_ticket_scenarios"
                           " (campaign_ticket_id, scenario_id, status)"
                           " SELECT %s, x, %s"
                           " FROM unnest(%s) x"
                           " on conflict do nothing;", (campaign_ticket_id[0],
                                                       ScenarioStatusEnum.recorded.value,
                                                       scenarios_id))
        await rs_invalidate_file(f"file:{provide(project_name)}:{version}:{occurrence}:*")


async def db_delete_campaign_ticket_scenario(project_name,
                                       version,
                                       occurrence,
                                       reference,
                                       scenario_internal_id):
    """Delete scenario from campaign_ticket"""
    campaign_ticket_id = await retrieve_campaign_ticket_id(project_name, version, occurrence, reference)
    if not db_is_scenario_internal_id_exist(project_name, scenario_internal_id):
        raise ScenarioNotFound(f"No scenario with id {scenario_internal_id} "
                               f"found in project {project_name}")
    with pool.connection() as connection:
        connection.row_factory = dict_row
        connection.execute("delete from campaign_ticket_scenarios "
                           "where campaign_id = %s "
                           "and scenario_id = %s ",
                           (campaign_ticket_id[0],
                            scenario_internal_id))
        await rs_invalidate_file(f"file:{provide(project_name)}:{version}:{occurrence}:*")


async def db_set_campaign_ticket_scenario_status(project_name,
                                           version,
                                           occurrence,
                                           reference,
                                           scenario_id,
                                           new_status):
    campaign_ticket_id = await retrieve_campaign_ticket_id(project_name, version, occurrence, reference)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        await rs_invalidate_file(f"file:{provide(project_name)}:{version}:{occurrence}:*")
        return connection.execute(
            "update campaign_ticket_scenarios as cts "
            "set status = %s "
            "from scenarios as sc "
            "where cts.campaign_ticket_id = %s "
            " and sc.scenario_id = %s "
            " and cts.scenario_id = sc.id "
            "returning sc.scenario_id as scenario_id, cts.status as status;",
            (new_status, campaign_ticket_id[0], scenario_id)).fetchone()


def db_is_scenario_internal_id_exist(project_name,
                                     scenario_internal_id):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute("select count(sc.id) as sc_count "
                                  "from scenarios as sc "
                                  "join features as ft on sc.feature_id = ft.id "
                                  "where sc.id = %s "
                                  "and ft.project_id = %s",
                                  [scenario_internal_id, project_name]).fetchone()
        return rows["sc_count"] == 1


async def db_update_campaign_occurrence(project_name: str,
                                        version: str,
                                        occurrence: str,
                                        update: CampaignPatch):
    campaign = await get_campaign_content(project_name, version, occurrence, True)
    version_transition(campaign.status,
                       update.status,
                       TicketType,
                       ticket_authorized_transition
                       )

    with pool.connection() as connection:
        connection.row_factory = dict_row
