# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Union

from psycopg.rows import dict_row, tuple_row

from app.app_exception import CampaignNotFound, NonUniqueError
from app.database.tickets import get_ticket, get_tickets_by_reference
from app.schema.campaign_field_filtering import validate_campaign_tickets_fields
from app.schema.postgres_enums import CampaignStatusEnum
from app.schema.project_schema import TestFeature, TestScenario
from app.schema.campaign_schema import TicketScenarioCampaign
from app.utils.pgdb import pool


def create_campaign(project_name, version):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        conn = connection.execute("insert into campaigns (project_id, version, status) "
                                  "values (%s, %s, %s)"
                                  "returning project_id as project_name, "
                                  "version as version, occurrence as occurrence, "
                                  "description as description, status as status;",
                                  (project_name.casefold(), version,
                                   CampaignStatusEnum.recorded)).fetchone()

        connection.commit()
        return conn


def retrieve_campaign(project_name,
                      version: str = None,
                      status: str = None,
                      limit: int = 10,
                      skip: int = 0):
    with pool.connection() as connection:
        connection.row_factory = dict_row
        if version is None and status is None:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, limit, skip))
        elif version is None:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s"
                                      " and status = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, status, limit, skip))
        elif status is None:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      " and version = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, version, limit, skip))
        else:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      " and version = %s"
                                      " and status = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, version, status, limit, skip))
        count = connection.execute("select count(*) as total "
                                   "from campaigns "
                                   "where project_id = %s;", (project_name,))
        return conn.fetchall(), count.fetchone()["total"]


def retrieve_campaign_id(project_name: str, version: str, occurrence: str):
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute("select id, status"
                                  " from campaigns"
                                  " where project_id = %s "
                                  " and version = %s "
                                  " and occurrence = %s;",
                                  (project_name, version, occurrence)).fetchone()


def is_campaign_exist(project_name: str, version: str, occurrence: str):
    return bool(retrieve_campaign_id(project_name, version, occurrence))


def fill_campaign(project_name: str,
                  version: str,
                  occurrence: str,
                  content: TicketScenarioCampaign):
    # Check ticket existence
    ticket = get_ticket(project_name, version, content.ticket_reference)
    if ticket is None:
        raise NonUniqueError(f"Found no ticket for project {project_name} in version {version} "
                             f"with reference {content.ticket_reference}.")

    with pool.connection() as connection:
        campaign_id = connection.execute("select id "
                                         "from campaigns "
                                         "where project_id = %s "
                                         "and version = %s "
                                         "and occurrence = %s;",
                                         (project_name, version, occurrence)).fetchone()
        if not bool(campaign_id):
            raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                                   f"for project {project_name} in version {version} not found")

        if isinstance(content.scenarios, list):
            scenarios = content.scenarios
        else:
            scenarios = list(content.scenarios)
        errors = []
        for scenario in scenarios:
            # Retrieve scenario id
            if scenario.feature_name and not scenario.feature_filename:
                scenario_id = connection.execute("select scenarios.id "
                                                 "from scenarios "
                                                 "join features on features.id = scenarios.feature_id "
                                                 "join epics on epics.id = features.epic_id "
                                                 "where epics.project_id = %s "
                                                 "and epics.name = %s "
                                                 "and features.name = %s "
                                                 "and scenarios.scenario_id = %s;",
                                                 (project_name,
                                                  scenario.epic,
                                                  scenario.feature_name,
                                                  scenario.scenario_id)).fetchall()
            else:
                scenario_id = connection.execute("select scenarios.id "
                                                 "from scenarios "
                                                 "join features on features.id = scenarios.feature_id "
                                                 "join epics on epics.id = features.epic_id "
                                                 "where epics.project_id = %s "
                                                 "and epics.name = %s "
                                                 "and features.name = %s "
                                                 "and features.filename like %s "
                                                 "and scenarios.scenario_id = %s;",
                                                 (project_name,
                                                  scenario.epic,
                                                  scenario.feature_name,
                                                  scenario.feature_filename,
                                                  scenario.scenario_id)).fetchall()
            if not scenario_id or len(scenario_id) > 1:
                errors.append(f"Found {len(scenario_id)} scenarios while expecting one and"
                                     f" only one.\n"
                                     f"Search criteria was {scenario}")
                break

            result = connection.execute("insert into campaign_tickets_scenarios "
                                        "(campaign_id, scenario_id, ticket_reference, status) "
                                        "values (%s, %s, %s, %s) "
                                        "on conflict (campaign_id, scenario_id, ticket_reference) "
                                        "do nothing;",
                                        (campaign_id[0], scenario_id[0][0],
                                         content.ticket_reference,
                                         CampaignStatusEnum.recorded))

        # I must do something with it


def get_campaign_content(project_name: str, version: str, occurrence: str):
    """Retrieve the campaign fully (tickets and scenarios). No pagination."""
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        # Select all sql data related to the campaign
        result = connection.execute("select ticket_reference as reference, status as status,"
                                    " sc.scenario_id as scenario_id, sc.name as name,"
                                    " sc.steps as steps, ft.name as feature_name, "
                                    "ep.name as epic_id "
                                    "from campaign_tickets_scenarios as cts "
                                    "join scenarios as sc "
                                    "   on sc.id = cts.scenario_id "
                                    "join features as ft "
                                    "   on sc.feature_id = ft.id "
                                    "join epics as ep "
                                    "   on ft.epic_id = ep.id "
                                    "where campaign_id = %s "
                                    "order by cts.ticket_reference desc;",
                                    (campaign_id[0],))
        # Prepare the result
        camp = {"project": project_name,
                "version": version,
                "occurrence": occurrence,
                "status": campaign_id[1],
                "tickets": []}
        # Accumulators
        tickets = set()
        current_ticket = {}
        # Iter over result and dispatch between new ticket and ticket's scenario
        for row in result.fetchall():
            if row["reference"] not in tickets:
                if current_ticket:
                    camp["tickets"].append(current_ticket)
                tickets.add(row['reference'])
                current_ticket = {"reference": row['reference'],
                                  "summary": None,
                                  "scenarios": []}
            current_ticket["scenarios"].append({
                "epic_id": row["epic_id"],
                "feature_id": row["feature_name"],
                "scenario_id": row["scenario_id"],
                "name": row["name"],
                "steps": row["steps"],
                "status": row["status"]
            })
        # Add the last ticket
        camp["tickets"].append(current_ticket)

        # Retrieve data from mongo
        tickets_data = {tick["reference"]: tick["description"]
                        for tick in get_tickets_by_reference(project_name, version, tickets)}

        # Update the tickets with their summary
        for tick in camp["tickets"]:
            if tick:
                tick["summary"] = tickets_data[tick["reference"]]
        return camp


def db_get_campaign_tickets(project_name,
                            version,
                            occurrence):
    """"""
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)

    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute("select distinct ticket_reference "
                                    "from campaign_tickets_scenarios as cts "
                                    "where campaign_id = %s "
                                    "order by cts.ticket_reference desc;",
                                    (campaign_id[0],))
        tickets = result.fetchall()
        updated_tickets = get_tickets_by_reference(project_name,
                                                   version,
                                                   [ticket[0] for ticket in tickets])
        return {"project": project_name,
                "version": version,
                "occurrence": occurrence,
                "status": campaign_id[1],
                "tickets": updated_tickets}


def db_get_campaign_ticket_scenarios(project_name,
                                     version,
                                     occurrence,
                                     reference):
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute("select sc.scenario_id as scenario_id, sc.name as name,"
                                    " sc.steps as steps, cts.status as status,"
                                    " ft.name as feature_name, "
                                    "ep.name as epic_id "
                                    "from campaign_tickets_scenarios as cts "
                                    "join scenarios as sc "
                                    "   on sc.id = cts.scenario_id "
                                    "join features as ft "
                                    "   on sc.feature_id = ft.id "
                                    "join epics as ep "
                                    "   on ft.epic_id = ep.id "
                                    "where cts.campaign_id = %s "
                                    "and cts.ticket_reference = %s ",
                                    (campaign_id[0], reference))
        return result.fetchall()


def db_get_campaign_ticket_scenario(project_name,
                                    version,
                                    occurrence,
                                    reference,
                                    scenario_id):
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute("select sc.scenario_id as scenario_id, sc.name as name,"
                                    " sc.steps as steps, cts.status as status "
                                    "from campaign_tickets_scenarios as cts "
                                    "join scenarios as sc "
                                    "   on sc.id = cts.scenario_id "
                                    "where cts.campaign_id = %s "
                                    "and cts.ticket_reference = %s "
                                    "and sc.scenario_id = %s",
                                    (campaign_id[0], reference, scenario_id))
        return result.fetchone()


def db_set_campaign_ticket_scenario_status(project_name,
                                           version,
                                           occurrence,
                                           reference,
                                           scenario_id,
                                           new_status):
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
        connection.row_factory = dict_row
        return connection.execute(
            "update campaign_tickets_scenarios as cts "
            "set status = %s "
            "from scenarios as sc "
            "where cts.campaign_id = %s "
            " and sc.scenario_id = %s "
            " and cts.scenario_id = sc.id "
            " and cts.ticket_reference = %s "
            "returning sc.scenario_id as scenario_id, cts.status as status, "
            "cts.ticket_reference as ticket_reference;",
            (new_status, campaign_id[0], scenario_id, reference)).fetchone()
