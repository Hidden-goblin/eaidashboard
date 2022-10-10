# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Union

from psycopg.rows import dict_row

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
        # Retrieve scenario id
        if content.feature_name and not content.feature_filename:
            scenario_id = connection.execute("select scenarios.id "
                                             "from scenarios "
                                             "join features on features.id = scenarios.feature_id "
                                             "join epics on epics.id = features.epic_id "
                                             "where epics.project_id = %s "
                                             "and epics.name = %s "
                                             "and features.name = %s "
                                             "and scenarios.scenario_id = %s;",
                                             (project_name,
                                              content.epic,
                                              content.feature_name,
                                              content.scenario_id)).fetchall()
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
                                              content.epic,
                                              content.feature_name,
                                              content.feature_filename,
                                              content.scenario_id)).fetchall()
        if not scenario_id or len(scenario_id) > 1:
            raise NonUniqueError(f"Found {len(scenario_id)} scenarios while expecting one and"
                                 f" only one.\n"
                                 f"Search criteria was {content}")

        result = connection.execute("insert into campaign_tickets_scenarios "
                                    "(campaign_id, scenario_id, ticket_reference, status) "
                                    "values (%s, %s, %s, %s) "
                                    "on conflict (campaign_id, scenario_id, ticket_reference) "
                                    "do nothing;",
                                    (campaign_id[0], scenario_id[0][0], content.ticket_reference,
                                     CampaignStatusEnum.recorded))

        # I must do something with it


def get_campaign_content(project_name: str, version: str, occurrence: str):
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)
    with pool.connection() as connection:
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
        camp = {"project": project_name,
                "version": version,
                "occurrence": occurrence,
                "status": campaign_id[1],
                "tickets": []}
        tickets = set()
        current_ticket = {}
        for row in result.fetchall():
            if row[0] not in tickets:
                if current_ticket:
                    camp["tickets"].append(current_ticket)
                tickets.add(row[0])
                current_ticket = {"reference": row[0],
                                  "summary": None,
                                  "scenarios": []}
            current_ticket["scenarios"].append({
                "epic_id": row[6],
                "feature_id": row[5],
                "scenario_id": row[2],
                "name": row[3],
                "steps": row[4],
                "status": row[1]
            })

        camp["tickets"].append(current_ticket)
        tickets_data = {tick["reference"]: tick["description"]
                        for tick in get_tickets_by_reference(project_name, version, tickets)}
        for tick in camp["tickets"]:
            tick["summary"] = tickets_data[tick["reference"]]
        return camp


def db_get_campaign_tickets(project_name, version, occurrence, fields: list[str] = ("reference",
                                                                                    "scenario_id",
                                                                                    "status")):
    if not is_campaign_exist(project_name, version, occurrence):
        raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                               f"for project {project_name} in version {version} not found")
    campaign_id = retrieve_campaign_id(project_name, version, occurrence)
    validate_campaign_tickets_fields(fields)

    field_mapping = {"status": 1,
                     "scenario_id": 2,
                     "name": 3,
                     "steps": 4,
                     "feature_id": 5,
                     "epic_id": 6}
    with pool.connection() as connection:
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
        return_tickets = []
        tickets = set()
        current_ticket = {}
        for row in result.fetchall():
            if row[0] not in tickets:
                if current_ticket:
                    return_tickets.append(current_ticket)
                tickets.add(row[0])
                if "reference" in fields:
                    current_ticket = {"reference": row[0],
                                      "scenarios": []}
                else:
                    current_ticket = {"scenarios": []}
            current_ticket["scenarios"].append(
                {field: row[field_mapping[field]] for field in fields if field in field_mapping})
        return_tickets.append(current_ticket)
        if "summary" in fields:
            tickets_data = {tick["reference"]: tick["description"]
                            for tick in get_tickets_by_reference(project_name, version, tickets)}
            for index, value in enumerate(tickets):
                return_tickets[index]["summary"] = tickets_data[value]

        return return_tickets


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
