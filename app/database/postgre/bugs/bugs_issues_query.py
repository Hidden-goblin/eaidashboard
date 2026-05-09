from logging import getLogger

from sqlalchemy import delete, literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert
from sqlalchemy.sql.dml import Delete
from sqlalchemy.sql.selectable import Select

from app.database.models.metadata import (
    bugs_issues,
    campaign_ticket_scenarios,
    campaign_tickets,
    campaigns,
    projects,
    scenarios,
)
from app.utils.project_alias import provide

logger = getLogger(__name__)


def build_get_bugs_issues_query_from_bug_id(bug_internal_id: int) -> Select:
    query = select(
        bugs_issues.c.occurrence,
        bugs_issues.c.ticket_reference,
        bugs_issues.c.scenario_id.label("scenario_tech_id"),
    ).where(bugs_issues.c.bug_id == bug_internal_id)

    return query


def build_insert_bug_issue_query(
    project_name: str,
    version: str,
    bug_id: int,
    occurrence: int,
    ticket_reference: str,
    scenario_tech_id: int,
) -> Insert:
    select_query = (
        select(
            literal(bug_id),
            literal(occurrence),
            literal(ticket_reference),
            literal(scenario_tech_id),
        )
        .select_from(campaign_ticket_scenarios)
        .join(campaign_tickets, campaign_tickets.c.id == campaign_ticket_scenarios.c.campaign_ticket_id)
        .join(campaigns, campaigns.c.id == campaign_tickets.c.campaign_id)
        .join(scenarios, scenarios.c.id == campaign_ticket_scenarios.c.scenario_id)
        .join(projects, projects.c.id == campaigns.c.project_id)
        .where(projects.c.alias == provide(project_name))
        .where(campaigns.c.version == version)
        .where(campaigns.c.occurrence == occurrence)
        .where(campaign_tickets.c.ticket_reference == ticket_reference)
        .where(scenarios.c.id == scenario_tech_id)
    )

    return (
        pg_insert(bugs_issues)
        .from_select(
            ["bug_id", "occurrence", "ticket_reference", "scenario_id"],
            select_query,
        )
        .on_conflict_do_nothing()
    )


def build_delete_bug_issue_query(
    bug_id: int,
    occurrence: int,
    ticket_reference: str,
    scenario_tech_id: int,
) -> Delete:
    return (
        delete(bugs_issues)
        .where(bugs_issues.c.bug_id == bug_id)
        .where(bugs_issues.c.occurrence == occurrence)
        .where(bugs_issues.c.ticket_reference == ticket_reference)
        .where(bugs_issues.c.scenario_id == scenario_tech_id)
    )
