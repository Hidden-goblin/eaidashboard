# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.app_exception import CampaignNotFound
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
    with pool.connection() as connection:
        result = connection.execute("select id "
                                    "from campaigns "
                                    "where project_id = %s "
                                    "and version = %s "
                                    "and occurrence = %s;",
                                    (project_name, version, occurrence)).fetchone()
        if not bool(result):
            raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                                   f"for project {project_name} in version {version} not found")
        # Retrieve scenario id

        scenario_id = connection.execute("select id "
                                         "from scenarios "
                                         
                                         "where project_id = %s "
                                         "and version = %s "
                                         "and occurrence = %s;",
                                         (project_name, version, occurrence)).fetchone()
