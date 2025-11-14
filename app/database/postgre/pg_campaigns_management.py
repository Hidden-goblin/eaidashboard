# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import copy
from logging import getLogger
from typing import List, Tuple

from psycopg.rows import dict_row, tuple_row

from app.schema.campaign.campaign_response_schema import CampaignLight
from app.schema.campaign_followup_schema import CampaignIdStatus
from app.schema.campaign_schema import CampaignPatch, CampaignProjection, CampaignProjections, OccurrenceStatus
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.pg_schema import PGResult
from app.schema.postgres_enums import CampaignStatusEnum, ScenarioStatusEnum
from app.schema.project_enum import ProjectProjections
from app.schema.status_enum import StatusEnum
from app.schema.ticket_schema import EnrichedTicket, Ticket
from app.utils.pgdb import pool
from app.utils.project_alias import provide

logger = getLogger(__name__)


async def create_campaign(
    project_name: str,
    version: str,
    status: str = "recorded",
) -> CampaignLight:
    """Insert into campaign a new empty occurrence"""
    with pool.connection() as connection:
        connection.row_factory = dict_row
        conn = connection.execute(
            """
        INSERT INTO campaigns (project_id, version, status, occurrence)
        SELECT p.id,
               %s,
               %s,
               COALESCE(
                   (SELECT MAX(c2.occurrence)
                    FROM campaigns c2
                    WHERE c2.project_id = p.id
                      AND c2.version = %s),
                   0
               ) + 1
        FROM projects p
        WHERE p.alias = %s
        RETURNING version, occurrence, description, status;""",
            (
                version,
                CampaignStatusEnum(status),
                version,
                provide(project_name),
            ),
        ).fetchone()

        connection.commit()
        return CampaignLight(
            **{
                "project_name": project_name,
                **conn,
            }
        )


async def retrieve_campaigns(
    project_name: str,
    projection: ProjectProjections,
    limit: int = 10,
    skip: int = 0,
) -> CampaignProjections:
    """retrieve basic campaigns data i.e. version, status and list of occurrences"""
    query = """SELECT
            v.version,
            JSON_AGG(JSON_BUILD_OBJECT(
      'occurrence', c.occurrence,
      'status', c.status
    ) ORDER BY c.occurrence) AS occurrences,
            v.status
        FROM projects p
        JOIN versions v ON v.project_id = p.id
        JOIN campaigns c ON c.project_id = p.id AND c.version = v.version"""
    query_count = """
    SELECT
            count(distinct v.version) as total
        FROM projects p
        JOIN versions v
            ON v.project_id = p.id
        JOIN campaigns c
            ON c.project_id = p.id
           AND c.version = v.version
    """
    where_clause: list[str] = ["p.alias = %s"]
    params: list[str | int | None] = [
        provide(project_name),
    ]
    group_order_clauses = """
    GROUP BY v.version, v.status, v.created
ORDER BY v.created DESC
    """
    if projection == ProjectProjections.ARCHIVED_CAMPAIGNS:
        where_clause.append("v.status = %s")
        params.append(StatusEnum.ARCHIVED.value)
    else:
        where_clause.append("v.status != %s")
        params.append(StatusEnum.ARCHIVED.value)

        params.extend([limit, skip])
    with pool.connection() as connection:
        connection.row_factory = dict_row
        conn = connection.execute(
            f"""
        {query} where {" and ".join(where_clause)} {group_order_clauses}
         LIMIT %s OFFSET %s;""",
            params,
        ).fetchall()
        conn_count = connection.execute(
            f"""{query_count} where {" and ".join(where_clause)};""", params[:-2]
        ).fetchone()

    return CampaignProjections(
        count=conn_count["total"],
        data=[
            CampaignProjection(
                version=elem["version"],
                occurrences=[OccurrenceStatus(**item) for item in elem["occurrences"]],
                status=elem["status"],
            )
            for elem in conn
        ],
    )


async def retrieve_campaign(
    project_name: str,
    version: str = None,
    status: str = None,
    limit: int = 10,
    skip: int = 0,
) -> Tuple[List[CampaignLight], int]:
    """
    Get raw campaign with version, occurrence, description, and status
    :return List[CampaignLight], <total result>
    """
    base_query = """
        select p.name as project_name,
               version as version,
               occurrence as occurrence,
               description as description,
               status as status
          from campaigns c
          join projects p on p.id = c.project_id
    """

    count_query = """
        select count(c.id) as total
          from campaigns c
          join projects p on p.id = c.project_id
    """

    conditions = [
        "p.alias = %s",
    ]
    params = [
        provide(project_name),
    ]

    # Dynamically add conditions based on inputs
    if version:
        conditions.append("version = %s")
        params.append(version)
    if status:
        conditions.append("c.status = %s")
        params.append(status)

    base_query = (
        f"{base_query} where {' and '.join(conditions)} order by version desc, occurrence desc limit %s offset %s;"
    )
    count_query = f"{count_query} where {' and '.join(conditions)};"

    params.extend([limit, skip])

    with pool.connection() as connection:
        connection.row_factory = dict_row

        # Execute queries
        # Todo add async fetch
        conn = connection.execute(base_query, tuple(params))
        count = connection.execute(count_query, tuple(params[:-2]))

    return [CampaignLight(**elem) for elem in conn.fetchall()], count.fetchone()["total"]


async def retrieve_campaigns_basics(
    project_name: str,
    campaign_projection: ProjectProjections = ProjectProjections.CAMPAIGNS,
    limit: int = 10,
    skip: int = 0,
) -> Tuple[List[dict], int]:
    """
    Retrieve the campaigns for a specific project.
    Ordered by creation date
    Args:
        project_name: the project name to look for
        campaign_projection:  default to "campaigns"
        limit: default to 10
        skip: default to 0
    """
    # base_query = """select version, count(occurrence) as occurrences from campaigns"""
    # conditions = ["project_id = %s"]
    # params = [project_name]

    pass


async def retrieve_campaign_id(
    project_name: str,
    version: str,
    occurrence: str,
) -> CampaignIdStatus | ApplicationError:
    """get campaign internal id and status"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        row = connection.execute(
            """select c.id, c.status
             from campaigns c
            join projects p on p.id = c.project_id
            where p.alias = %s  and c.version = %s  and c.occurrence = %s;""",
            (
                provide(project_name),
                version,
                occurrence,
            ),
        ).fetchone()
        if row is None:
            return ApplicationError(
                error=ApplicationErrorCode.occurrence_not_found,
                message=f"Occurrence '{occurrence}' not found",
            )
        return CampaignIdStatus(
            campaign_id=row[0],
            status=CampaignStatusEnum(row[1]),
        )


async def is_campaign_exist(
    project_name: str,
    version: str,
    occurrence: str,
) -> bool:
    """Check if campaign exist"""
    return isinstance(
        await retrieve_campaign_id(
            project_name,
            version,
            occurrence,
        ),
        CampaignIdStatus,
    )


async def enrich_tickets_with_campaigns(
    project_name: str,
    version: str,
    tickets: List[Ticket],
) -> List[EnrichedTicket]:
    """Add to ticket campaigns data"""
    _tickets = []
    with pool.connection() as connection:
        connection.row_factory = dict_row
        for ticket in tickets:
            rows = connection.execute(
                "select cp.occurrence as occurrence "
                "from campaigns as cp "
                "join projects as p on p.id = cp.project_id "
                "inner join campaign_tickets as cpt "
                " on cpt.campaign_id = cp.id "
                " where cp.version = %s "
                " and p.alias = %s "
                " and cpt.ticket_reference = %s",
                (
                    version,
                    provide(project_name),
                    ticket.reference,
                ),
            )
            occ = [row["occurrence"] for row in rows]
            _tickets.append(
                EnrichedTicket(
                    **{
                        **ticket.model_dump(),
                        "campaign_occurrences": occ,
                    },
                ),
            )

    return _tickets


async def update_campaign_occurrence(
    project_name: str,
    version: str,
    occurrence: str,
    update_occurrence: CampaignPatch,
) -> PGResult | ApplicationError:
    # Ensure the campaign exist
    campaign_id = await retrieve_campaign_id(
        project_name,
        version,
        occurrence,
    )
    if isinstance(campaign_id, ApplicationError):
        return campaign_id

    # Prepare request
    query = []
    values = []
    if update_occurrence.status is not None:
        query.append("status = %s")
        values.append(
            update_occurrence.status.value,
        )
    if update_occurrence.description is not None:
        query.append("description = %s")
        values.append(
            update_occurrence.description,
        )
    values.append(campaign_id.campaign_id)
    query_full = f"update campaigns set {', '.join(query)} where id = %s;"

    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            query_full,
            values,
        )
        logger.info(
            rows.statusmessage,
        )
        connection.commit()

    return (
        PGResult(
            message="Update done",
        )
        if rows.statusmessage == "UPDATE 1"
        else ApplicationError(
            message=rows.statusmessage,
            error=ApplicationErrorCode.database_no_update,
        )
    )


def merge_failing_scenario(
    general_result: list,
    already_linked: list,
) -> None:
    for scenario in already_linked:
        tmp = copy.deepcopy(scenario)
        tmp["selection"] = ""
        if tmp in general_result:
            general_result[general_result.index(tmp)] = scenario
        else:
            general_result.append(scenario)


def campaign_failing_scenarios(
    project_name: str,
    version: str,
    bug_internal_id: int = None,
) -> List[dict]:
    """Retrieve failing scenarios for a campaign
    If bug_internal_id is set then add as 'selected' already scenarios attached to the bug
    TODO add this mechanism /!\\ WARNING on future link (version might differ)
    TODO update project_id from project_name
    """
    query = (
        "select scenarios.name,"
        " scenarios.scenario_id as scenario_id,"
        " ct.ticket_reference,"
        " campaigns.occurrence,"
        " campaigns.version,"
        " cts.scenario_id as scenario_tech_id,"
        " '' as selection"
        " from campaign_ticket_scenarios as cts"
        " join campaign_tickets as ct on cts.campaign_ticket_id = ct.id"
        " join campaigns on campaigns.id = ct.campaign_id"
        " join scenarios on scenarios.id = cts.scenario_id"
        " where campaigns.project_id = %s"
        " and campaigns.version = %s"
        " and cts.status = %s;"
    )

    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            query,
            (
                project_name,
                version,
                ScenarioStatusEnum.waiting_fix,
            ),
        )
        result = rows.fetchall()
        if bug_internal_id is not None:
            query_linked = (
                "select scenarios.name,"
                " scenarios.scenario_id as scenario_id,"
                " ct.ticket_reference,"
                " campaigns.occurrence,"
                " campaigns.version,"
                " cts.scenario_id as scenario_tech_id,"
                " 'selected' as selection"
                " from campaign_ticket_scenarios as cts"
                " join campaign_tickets as ct on cts.campaign_ticket_id = ct.id"
                " join campaigns on campaigns.id = ct.campaign_id"
                " join scenarios on scenarios.id = cts.scenario_id"
                " where cts.scenario_id = %(scenario_id)s"
                " and ct.ticket_reference = %(ticket_reference)s;"
            )
            query_bug = "select scenario_id, ticket_reference from bugs_issues where bug_id = %s;"
            rows = connection.execute(
                query_bug,
                (bug_internal_id,),
            )
            issues_linked = list(rows.fetchall())
            accumulator = []
            if issues_linked:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.executemany(
                        query_linked,
                        issues_linked,
                        returning=True,
                    )
                    while True:
                        accumulator.extend(cursor.fetchall())
                        if not cursor.nextset():
                            break

            merge_failing_scenario(
                result,
                accumulator,
            )
        return result
