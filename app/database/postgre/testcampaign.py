# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import asyncio
from collections import Counter
from typing import List

from psycopg.rows import dict_row, tuple_row

from app.app_exception import CampaignNotFound, ScenarioNotFound
from app.database.postgre.pg_campaigns_management import is_campaign_exist, retrieve_campaign_id
from app.database.postgre.pg_tickets import get_ticket, get_tickets_by_reference
from app.database.redis.rs_file_management import rs_invalidate_file
from app.database.utils.ticket_management import add_ticket_to_campaign
from app.database.utils.transitions import ticket_authorized_transition, version_transition
from app.schema.base_schema import CreateUpdateModel
from app.schema.campaign_schema import (
    CampaignFull,
    CampaignPatch,
    TicketScenario,
    TicketScenarioCampaign,
)
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.schema.postgres_enums import ScenarioStatusEnum
from app.schema.respository.feature_schema import Feature
from app.schema.respository.scenario_schema import ScenarioExecution
from app.schema.status_enum import TicketType
from app.utils.pgdb import pool
from app.utils.project_alias import provide


async def fill_campaign(
    project_name: str,
    version: str,
    occurrence: str,
    content: TicketScenarioCampaign,
) -> CreateUpdateModel | ApplicationError:
    """Attach ticket to campaign
    Should not attach scenarios to campaign
    TODO: remove the attach scenarios and use dedicated function"""
    # Add ticket to campaign
    campaign_ticket_id = await add_ticket_to_campaign(
        project_name,
        version,
        occurrence,
        content.ticket_reference,
    )

    if isinstance(campaign_ticket_id, ApplicationError):
        return campaign_ticket_id
    return CreateUpdateModel(
        resource_id=campaign_ticket_id,
        message=f"Ticket {content.ticket_reference} has been linked to the occurrence {occurrence}"
        f" of the {version} campaign",
    )
    # return FillCampaignResult(campaign_ticket_id=campaign_ticket_id, errors=[])

    # if isinstance(content.scenarios, list | BaseScenario):
    #     scenarios = content.to_features(project_name) # Cast to Feature /!\ might be several features
    # # elif isinstance(content.scenarios, BaseScenario):
    # #     scenarios = [content.scenarios] # Cast to Feature
    # else:

    # Attach scenario to ticket
    # attached_scenarios = await db_put_campaign_ticket_scenarios(project_name, version, occurrence, content.ticket_reference, scenarios,)
    # Call db_put_campaign_ticket_scenarios() / check to split in two functions one with a direct call with campaign_ticket_id
    # errors = []
    # try:
    #     with pool.connection() as connection:
    #         for scenario in scenarios:
    #             # Retrieve scenario_internal_id id
    #             scenario_id = await db_get_scenarios_id(
    #                 project_name,
    #                 scenario.epic,
    #                 scenario.feature_name,
    #                 scenario.scenario_id,
    #                 scenario.filename,
    #             )
    #
    #             if not scenario_id or len(scenario_id) > 1:
    #                 errors.append(
    #                     f"Found {len(scenario_id)} scenarios while expecting one and"
    #                     f" only one.\n"
    #                     f"Search criteria was {scenario}",
    #                 )
    #                 break
    #
    #             result = connection.execute(
    #                 "insert into campaign_ticket_scenarios "
    #                 "(campaign_ticket_id, scenario_id,status) "
    #                 "values (%s, %s, %s) "
    #                 "on conflict (campaign_ticket_id, scenario_id) "
    #                 "do nothing;",
    #                 (
    #                     campaign_ticket_id,
    #                     scenario_id[0],
    #                     CampaignStatusEnum.recorded,
    #                 ),
    #             )
    #             log_message(result)
    # except Exception as exception:
    #     errors.append(exception.args)
    #     return ApplicationError(
    #         error=ApplicationErrorCode.database_error,
    #         message=f"Exception: {str(exception)}\n Errors: {'\n'.join(errors)}",
    #     )

    # return (
    #     FillCampaignResult(
    #         campaign_ticket_id=campaign_ticket_id,
    #         errors=errors,
    #     )
    #     if not isinstance(
    #         campaign_ticket_id,
    #         ApplicationError,
    #     )
    #     else campaign_ticket_id
    # )


async def db_put_campaign_ticket_scenarios(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
    scenarios: List[Feature],
) -> ApplicationError | CreateUpdateModel:
    """
    Attach scenario to tickets in a campaign
    Args:
        project_name:
        version:
        occurrence:
        reference:
        scenarios:

    Returns:

    """
    campaign_ticket_id = await retrieve_campaign_ticket_id(
        project_name,
        version,
        occurrence,
        reference,
    )
    if isinstance(campaign_ticket_id, ApplicationError):
        return campaign_ticket_id

    # Call sub function
    scenarios_id = []
    not_found_scenario_ids = set()
    # Get scenario_internal_id ids
    for feature in scenarios:
        feature.project_name = project_name
        await feature.gather_scenarios_from_ids()
        scenarios_id.extend(feature.scenario_tech_ids())
        not_found_scenario_ids.update(feature.deleted_scenarios())

    if scenarios_id:  # Guard clause
        with pool.connection() as connection:
            connection.row_factory = dict_row
            connection.execute(
                "insert into campaign_ticket_scenarios"
                " (campaign_ticket_id, scenario_id, status)"
                " SELECT %s, x, %s"
                " FROM unnest(%s) x"
                " on conflict do nothing;",
                (
                    campaign_ticket_id[0],
                    ScenarioStatusEnum.recorded.value,
                    scenarios_id,
                ),
            )
        rs_invalidate_file(f"file:{provide(project_name)}:{version}:{occurrence}:*")
    message = f"Attached {len(scenarios_id)} scenario to ticket."
    if not_found_scenario_ids:
        message = f"One or more scenario cannot be found.\n {message}"
    return CreateUpdateModel(
        resource_id=campaign_ticket_id[0], message=message, raw_data={"not_found_scenario": not_found_scenario_ids}
    )
    # return RegisterVersionResponse(
    #     inserted_id=campaign_ticket_id[0], acknowledged=True, message="Miss linked scenario ids"
    # )


async def retrieve_campaign_ticket_id(
    project_name: str,
    version: str,
    occurrence: str,
    ticket_reference: str,
) -> tuple | ApplicationError:
    if not await is_campaign_exist(
        project_name,
        version,
        occurrence,
    ):
        return ApplicationError(
            error=ApplicationErrorCode.campaign_not_found,
            message=f"Campaign occurrence {occurrence} for project {project_name} in version {version} not found",
        )
    async with asyncio.TaskGroup() as tg:
        campaign_id = tg.create_task(
            retrieve_campaign_id(
                project_name,
                version,
                occurrence,
            ),
        )

        ticket = tg.create_task(
            get_ticket(
                project_name,
                version,
                ticket_reference,
            ),
        )

    if isinstance(ticket.result(), ApplicationError):
        return ticket.result()

    if isinstance(campaign_id.result(), ApplicationError):
        return campaign_id.result()

    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute(
            "select id from campaign_tickets where campaign_id = %s and ticket_reference = %s;",
            (
                campaign_id.result().campaign_id,
                ticket_reference,
            ),
        ).fetchone()


async def get_campaign_content(
    project_name: str,
    version: str,
    occurrence: str,
    only_status: bool = False,
) -> ApplicationError | CampaignFull:
    """Retrieve the campaign fully (tickets and scenarios). No pagination yet."""
    # Unique id for project/version/occurrence triplet
    campaign_id = await retrieve_campaign_id(
        project_name,
        version,
        occurrence,
    )
    if isinstance(campaign_id, ApplicationError):
        return campaign_id

    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute(
            "select description from campaigns where id = %s",
            (campaign_id.campaign_id,),
        )
        # Prepare the result
        camp = CampaignFull(
            project_name=project_name,
            version=version,
            description=result.fetchone()["description"],
            occurrence=int(occurrence),
            status=campaign_id.status,
        )
        if only_status:
            return camp
        # Select all sql data related to the campaign
        result = connection.execute(
            "select ct.ticket_reference as reference, "
            "ct.id as campaign_id,"
            "tk.description as summary "
            "from campaign_tickets as ct "
            "join tickets as tk on ct.ticket_id = tk.id "
            "where ct.campaign_id = %s "
            "order by ct.ticket_reference desc;",
            (campaign_id.campaign_id,),
        )
        # Accumulators
        tickets = set()
        current_ticket = None
        # Iter over result and dispatch between new ticket and ticket's scenario_internal_id
        for row in result.fetchall():
            if row["reference"] not in tickets:
                if current_ticket:
                    camp.tickets.append(current_ticket)
                tickets.add(row["reference"])
                current_ticket = TicketScenario(
                    reference=row["reference"],
                    summary=row["summary"],
                    scenarios=await db_get_campaign_ticket_scenarios(
                        project_name,
                        version,
                        occurrence,
                        row["reference"],
                    ),
                )
        # Add the last ticket
        if current_ticket is not None:
            camp.tickets.append(current_ticket)

        return camp


def db_get_campaign_scenarios(
    campaign_id: int,
) -> List[ScenarioExecution]:
    """:return list of dict epic_id, feature_id, scenario_id, name, steps and status"""
    # TODO check the return schema to use app.schema.repository.scenario_schema
    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute(
            "select ep.name as epic,"
            " ft.name as feature_name,"
            " sc.scenario_id as scenario_id,"
            " sc.name as name,"
            " sc.steps as steps,"
            " cts.status as status"
            " from campaign_ticket_scenarios as cts"
            " join scenarios as sc on sc.id = cts.scenario_id"
            " join features as ft on sc.feature_id = ft.id"
            " join epics as ep on ft.epic_id = ep.id"
            " join campaign_tickets as ct on ct.id = cts.campaign_ticket_id"
            " where ct.campaign_id = %s;",
            (campaign_id,),
        )
        return [ScenarioExecution(**item) for item in result.fetchall()]


async def db_get_campaign_tickets(
    project_name: str,
    version: str,
    occurrence: str,
) -> CampaignFull | ApplicationError:
    """"""
    if not await is_campaign_exist(
        project_name,
        version,
        occurrence,
    ):
        return ApplicationError(
            error=ApplicationErrorCode.campaign_not_found,
            message=f"Campaign occurrence {occurrence} for project {project_name} in version {version} not found",
        )
    campaign_id = await retrieve_campaign_id(
        project_name,
        version,
        occurrence,
    )
    if isinstance(campaign_id, ApplicationError):
        return campaign_id

    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute(
            "select distinct ticket_reference "
            "from campaign_tickets as ct "
            "where campaign_id = %s "
            "order by ct.ticket_reference desc;",
            (campaign_id.campaign_id,),
        )
        tickets = result.fetchall()
        updated_tickets = list(
            await get_tickets_by_reference(
                project_name,
                version,
                [ticket[0] for ticket in tickets],
            ),
        )

        return CampaignFull(
            project_name=project_name,
            version=version,
            occurrence=occurrence,
            status=campaign_id.status,
            tickets=updated_tickets,
        )


async def db_get_campaign_ticket_scenarios(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
) -> List[ScenarioExecution] | ApplicationError:
    """Retrieve scenarios associated to a ticket in a campaign"""
    if not await is_campaign_exist(
        project_name,
        version,
        occurrence,
    ):
        return ApplicationError(
            error=ApplicationErrorCode.campaign_not_found,
            message=f"Campaign occurrence {occurrence} for project {project_name} in version {version} not found",
        )
    campaign_id = await retrieve_campaign_id(
        project_name,
        version,
        occurrence,
    )
    if isinstance(campaign_id, ApplicationError):
        return campaign_id

    with pool.connection() as connection:
        connection.row_factory = dict_row
        exist = connection.execute(
            "select 1  from campaign_tickets where campaign_id = %s and ticket_reference = %s;",
            (
                campaign_id.campaign_id,
                reference,
            ),
        )
        result = connection.execute(
            "select sc.scenario_id as scenario_id,"
            " sc.name as name,"
            " sc.steps as steps,"
            " cts.status as status,"
            " ft.name as feature_name,"
            " sc.id as scenario_tech_id,"
            " ep.name as epic"
            " from campaign_tickets as ct"
            " join campaign_ticket_scenarios as cts"
            " on ct.id = cts.campaign_ticket_id"
            " join scenarios as sc on sc.id = cts.scenario_id"
            " join features as ft on sc.feature_id = ft.id"
            " join epics as ep on ft.epic_id = ep.id"
            " where ct.campaign_id = %s"
            " and ct.ticket_reference = %s;",
            (
                campaign_id.campaign_id,
                reference,
            ),
        )
        return (
            [ScenarioExecution(**res) for res in result.fetchall()]
            if exist.fetchone()
            else ApplicationError(
                error=ApplicationErrorCode.ticket_not_found,
                message=f"Could not find {reference} in the campaign",
            )
        )


async def db_get_campaign_ticket_scenarios_status_count(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
) -> dict:
    if not await is_campaign_exist(
        project_name,
        version,
        occurrence,
    ):
        raise CampaignNotFound(
            f"Campaign occurrence {occurrence} for project {project_name} in version {version} not found"
        )
    campaign_id = await retrieve_campaign_id(
        project_name,
        version,
        occurrence,
    )
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        result = connection.execute(
            "select cts.status"
            " from campaign_tickets as ct"
            " join campaign_ticket_scenarios as cts"
            " on ct.id = cts.campaign_ticket_id"
            " join scenarios as sc on sc.id = cts.scenario_id"
            " join features as ft on sc.feature_id = ft.id"
            " join epics as ep on ft.epic_id = ep.id"
            " where ct.campaign_id = %s"
            " and ct.ticket_reference = %s;",
            (
                campaign_id.campaign_id,
                reference,
            ),
        )
        temp = [res[0] for res in result.fetchall()]
        return dict(Counter(temp))


async def db_get_campaign_ticket_scenario(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
    scenario_internal_id: str,
) -> dict | ApplicationError:
    """Todo Add schema to ticket_scenario"""
    if not await is_campaign_exist(
        project_name,
        version,
        occurrence,
    ):
        return ApplicationError(
            error=ApplicationErrorCode.campaign_not_found,
            message=f"Campaign occurrence {occurrence} for project {project_name} in version {version} not found",
        )
    campaign_ticket_id = await retrieve_campaign_ticket_id(
        project_name,
        version,
        occurrence,
        reference,
    )
    if isinstance(campaign_ticket_id, ApplicationError):
        return campaign_ticket_id

    with pool.connection() as connection:
        connection.row_factory = dict_row
        result = connection.execute(
            "select sc.scenario_id as scenario_id,"
            " sc.name as name,"
            " sc.steps as steps,"
            " cts.status as status,"
            " cts.scenario_id as scenario_internal_id"
            " from campaign_ticket_scenarios as cts"
            " join scenarios as sc on sc.id = cts.scenario_id"
            " where cts.campaign_ticket_id = %s"
            " and cts.scenario_id = %s;",
            (
                campaign_ticket_id[0],
                scenario_internal_id,
            ),
        )
        return result.fetchone()


async def db_delete_campaign_ticket_scenario(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
    scenario_internal_id: int,
) -> None:
    """Delete scenario from campaign_ticket"""
    campaign_ticket_id = await retrieve_campaign_ticket_id(
        project_name,
        version,
        occurrence,
        reference,
    )
    if not db_is_scenario_internal_id_exist(
        project_name,
        scenario_internal_id,
    ):
        raise ScenarioNotFound(f"No scenario with id {scenario_internal_id} found in project {project_name}")
    with pool.connection() as connection:
        connection.row_factory = dict_row
        connection.execute(
            "delete from campaign_ticket_scenarios where campaign_ticket_id = %s and scenario_id = %s ",
            (
                campaign_ticket_id[0],
                scenario_internal_id,
            ),
        )
        rs_invalidate_file(f"file:{provide(project_name)}:{version}:{occurrence}:*")


async def db_set_campaign_ticket_scenario_status(
    project_name: str,
    version: str,
    occurrence: str,
    reference: str,
    scenario_internal_id: str,
    new_status: str,
) -> dict | ApplicationError:
    # TODO: create model to replace 'dict' response
    campaign_ticket_id = await retrieve_campaign_ticket_id(
        project_name,
        version,
        occurrence,
        reference,
    )
    if isinstance(campaign_ticket_id, ApplicationError):
        return campaign_ticket_id
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rs_invalidate_file(f"file:{provide(project_name)}:{version}:{occurrence}:*")
        result = connection.execute(
            "update campaign_ticket_scenarios as cts "
            "set status = %s "
            # "from scenarios as sc "
            "where cts.campaign_ticket_id = %s "
            # " and sc.scenario_id = %s "
            " and cts.scenario_id = %s "
            "returning cts.status as status;",
            (
                new_status,
                campaign_ticket_id[0],
                scenario_internal_id,
            ),
        ).fetchone()
    return (
        result
        if result
        else ApplicationError(
            error=ApplicationErrorCode.ticket_not_found,
            message="Cannot find the scenario linked to the campaign to update the status",
        )
    )


def db_is_scenario_internal_id_exist(
    project_name: str,
    scenario_internal_id: int,
) -> bool:
    with pool.connection() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(
            "select count(sc.id) as sc_count "
            "from scenarios as sc "
            "join features as ft on sc.feature_id = ft.id "
            "where sc.id = %s "
            "and ft.project_id = %s",
            [
                scenario_internal_id,
                project_name,
            ],
        ).fetchone()
        return rows["sc_count"] == 1


async def db_update_campaign_occurrence(
    project_name: str,
    version: str,
    occurrence: str,
    update: CampaignPatch,
) -> None:
    campaign = await get_campaign_content(
        project_name,
        version,
        occurrence,
        True,
    )
    version_transition(
        campaign.status,
        update.status,
        TicketType,
        ticket_authorized_transition,
    )

    with pool.connection() as connection:
        connection.row_factory = dict_row
