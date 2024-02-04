# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import copy
from logging import getLogger
from typing import List, Tuple

from psycopg.rows import dict_row, tuple_row

from app.schema.campaign_schema import CampaignLight, CampaignPatch
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum
from app.schema.ticket_schema import EnrichedTicket, Ticket
from app.utils.pgdb import pool

logger = getLogger(__name__)


async def create_campaign(project_name: str,
                          version: str,
                          status: str = "recorded") -> CampaignLight:
    """Insert into campaign a new empty occurrence"""
    with pool.connection() as connection:
        connection.row_factory = dict_row
        conn = connection.execute("insert into campaigns (project_id, version, status, occurrence) "
                                  "select %s, %s, %s, coalesce(max(occurrence), 0) +1 "
                                  "from campaigns where project_id = %s and version = %s "
                                  "returning project_id as project_name, "
                                  "version as version, occurrence as occurrence, "
                                  "description as description, status as status;",
                                  (project_name.casefold(),
                                   version,
                                   CampaignStatusEnum(status),
                                   project_name.casefold(),
                                   version)).fetchone()

        connection.commit()
        return CampaignLight(**conn)


async def retrieve_campaign(project_name: str,
                            version: str = None,
                            status: str = None,
                            limit: int = 10,
                            skip: int = 0) -> Tuple[List[CampaignLight], int]:
    """Get raw campaign with version, occurrence, description and status
    TODO: check if dict could be replace with a model
    """
    with pool.connection() as connection:
        connection.row_factory = dict_row
        if version is None and status is None:
            conn = connection.execute("select project_id as project_name,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, limit, skip))
        elif version is None:
            conn = connection.execute("select project_id as project_name,"
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
            conn = connection.execute("select project_id as project_name,"
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
            conn = connection.execute("select project_id as project_name,"
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
        return [CampaignLight(**elem) for elem in conn.fetchall()], count.fetchone()["total"]


async def retrieve_campaign_id(project_name: str,
                               version: str,
                               occurrence: str) -> Tuple[int, str] | ApplicationError:
    """get campaign internal id and status"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        row = connection.execute("select id, status"
                                 " from campaigns"
                                 " where project_id = %s "
                                 " and version = %s "
                                 " and occurrence = %s;",
                                 (project_name, version, occurrence)).fetchone()
        if row is None:
            return ApplicationError(error=ApplicationErrorCode.occurrence_not_found,
                                    message=f"Occurrence '{occurrence}' not found")
        return row


async def retrieve_all_campaign_id_for_version(project_name: str,
                                               version: str) -> List[Tuple[int, str]]:
    """Get campaigns internal id and status"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute("select id, status"
                                  " from campaigns"
                                  " where project_id = %s "
                                  " and version = %s ",
                                  (project_name, version)).fetchall()


async def is_campaign_exist(project_name: str,
                            version: str,
                            occurrence: str) -> bool:
    """Check if campaign exist"""
    try:
        return bool(await retrieve_campaign_id(project_name, version, occurrence))
    except Exception:
        return False


async def enrich_tickets_with_campaigns(project_name: str,
                                        version: str,
                                        tickets: List[Ticket]) -> List[EnrichedTicket]:
    """Add to ticket campaigns data"""
    _tickets = []
    with pool.connection() as connection:
        connection.row_factory = dict_row
        for ticket in tickets:
            rows = connection.execute("select cp.occurrence as occurrence "
                                      "from campaigns as cp "
                                      "inner join campaign_tickets as cpt "
                                      " on cpt.campaign_id = cp.id "
                                      " where cp.version = %s "
                                      " and cp.project_id = %s "
                                      " and cpt.ticket_reference = %s",
                                      (version, project_name, ticket.reference))
            occ = [row['occurrence'] for row in rows]
            _tickets.append(EnrichedTicket(**{**ticket.model_dump(),
                                              "campaign_occurrences": occ}))

    return _tickets


async def update_campaign_occurrence(project_name: str,
                                     version: str,
                                     occurrence: str,
                                     update_occurrence: CampaignPatch) -> List[
                                                                              str] | \
                                                                          ApplicationError:
    campaign_id = await retrieve_campaign_id(project_name, version, occurrence)
    if isinstance(campaign_id, ApplicationError):
        return campaign_id
    with pool.connection() as connection:
        connection.row_factory = dict_row
        query = []
        values = []
        if update_occurrence.status is not None:
            query.append("status = %s")
            values.append(update_occurrence.status.value)
        if update_occurrence.description is not None:
            query.append("description = %s")
            values.append(update_occurrence.description)
        values.append(campaign_id[0])
        query_full = ("update campaigns"
                      f" set {', '.join(query)}"
                      " where id = %s;")
        rows = connection.execute(query_full,
                                  values)
        logger.info(rows.statusmessage)
        connection.commit()

    return rows


def merge_failing_scenario(general_result: list, already_linked: list) -> None:
    for scenario in already_linked:
        tmp = copy.deepcopy(scenario)
        tmp["selection"] = ''
        if tmp in general_result:
            general_result[general_result.index(tmp)] = scenario
        else:
            general_result.append(scenario)


def campaign_failing_scenarios(project_name: str, version: str, bug_internal_id: int = None) -> List[dict]:
    """Retrieve failing scenarios for a campaign
    If bug_internal_id is set then add as 'selected' already scenarios attached to the bug
    TODO add this mechanism /!\\ WARNING on future link (version might differ)
    """
    query = ("select scenarios.name,"
             " scenarios.scenario_id as scenario_id,"
             " ct.ticket_reference,"
             " campaigns.occurrence,"
             " campaigns.version,"
             " cts.scenario_id as scenario_tech_id,"
             " '' as selection"
             " from campaign_ticket_scenarios as cts"
             " join campaign_tickets as ct on cts.campaign_ticket_id = ct.id"
             " join campaigns on campaigns.id = ct.campaign_id"
             " join scenarios on scenarios.id = cts.id"
             " where campaigns.project_id = %s"
             " and campaigns.version = %s"
             " and cts.status = %s;")

    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(query,
                                  (project_name,
                                   version,
                                   ScenarioStatusEnum.waiting_fix))
        result = rows.fetchall()
        if bug_internal_id is not None:
            query_linked = ("select scenarios.name,"
                            " scenarios.scenario_id as scenario_id,"
                            " ct.ticket_reference,"
                            " campaigns.occurrence,"
                            " campaigns.version,"
                            " cts.scenario_id as scenario_tech_id,"
                            " 'selected' as selection"
                            " from campaign_ticket_scenarios as cts"
                            " join campaign_tickets as ct on cts.campaign_ticket_id = ct.id"
                            " join campaigns on campaigns.id = ct.campaign_id"
                            " join scenarios on scenarios.id = cts.id"
                            " where cts.scenario_id = %(scenario_id)s"
                            " and ct.ticket_reference = %(ticket_reference)s;")
            query_bug = ("select scenario_id, ticket_reference"
                         " from bugs_issues"
                         " where bug_id = %s;")
            rows = connection.execute(query_bug, (bug_internal_id,))
            issues_linked = list(rows.fetchall())
            accumulator = []
            if issues_linked:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.executemany(query_linked, issues_linked, returning=True)
                    while True:
                        accumulator.extend(cursor.fetchall())
                        if not cursor.nextset():
                            break

            merge_failing_scenario(result, accumulator)
        return result
