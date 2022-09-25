# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.app_exception import CampaignNotFound, NonUniqueError
from app.database.tickets import get_ticket
from app.schema.postgres_enums import CampaignStatus
from app.schema.project_schema import TestFeature, TestScenario, TicketScenarioCampaign
from app.utils.pgdb import pool


def create_campaign(project_name, version):
    with pool.connection() as connection:
        conn = connection.execute("insert into campaigns (project_id, version, status) "
                                  "values (%s, %s, %s)"
                                  "returning *;",
                                  (project_name.casefold(), version,
                                   CampaignStatus.recorded)).fetchone()

        connection.commit()
        return {"id": conn[0], "project_id": conn[1], "version": conn[2], "occurrence": conn[3],
                "description": conn[4], "status": conn[5]}


def retrieve_campaign(project_name, version: str = None, status: str = None):
    with pool.connection() as connection:
        if version is None and status is None:
            conn = connection.execute("select id, project_id, version, occurrence, description ,"
                                      " status "
                                      "from campaigns "
                                      "where project_id = %s;", (project_name,))
        elif version is None:
            conn = connection.execute("select id, project_id, version, occurrence, description ,"
                                      " status "
                                      "from campaigns "
                                      "where project_id = %s"
                                      " and status = %s;", (project_name, status))
        elif status is None:
            conn = connection.execute("select id, project_id, version, occurrence, description ,"
                                      " status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      " and version = %s;", (project_name, version))
        else:
            conn = connection.execute("select id, project_id, version, occurrence, description ,"
                                      " status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      " and version = %s"
                                      " and status = %s;", (project_name, version, status))
        return [{"id": rep[0], "project_id": rep[1], "version": rep[2], "occurrence": rep[3],
                 "description": rep[4], "status": rep[5]} for rep in conn.fetchall()]


def is_campaign_exist(project_name: str, version: str, occurrence: str):
    with pool.connection() as connection:
        result = connection.execute("select id"
                                    " from campaigns"
                                    " where project_id = %s "
                                    " and version = %s "
                                    " and occurrence = %s;",
                                    (project_name, version, occurrence)).fetchone()
        return bool(result)


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
                                     CampaignStatus.recorded))

        # I must do something with it

def get_campaign_content(project_name: str, version: str, occurrence: str):
    pass
