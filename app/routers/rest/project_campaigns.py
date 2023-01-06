# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
from typing import (Any, List)

from fastapi import (APIRouter,
                     HTTPException,
                     Response,
                     Security)

from app.app_exception import (CampaignNotFound, NonUniqueError, VersionNotFound)
from app.database.authorization import authorize_user
from app.database.postgre.testcampaign import (db_get_campaign_ticket_scenario,
                                               db_get_campaign_ticket_scenarios, db_get_campaign_tickets,
                                               db_put_campaign_ticket_scenarios,
                                               db_set_campaign_ticket_scenario_status, get_campaign_content,

                                               fill_campaign as db_fill_campaign)
from app.database.postgre.pg_campaigns_management import create_campaign, is_campaign_exist, \
    retrieve_campaign
from app.database.mongo.versions import get_version_and_collection
from app.schema.postgres_enums import (CampaignStatusEnum, ScenarioStatusEnum)
from app.schema.project_schema import (ErrorMessage)
from app.schema.campaign_schema import (CampaignLight, Scenarios,
                                        TicketScenarioCampaign,
                                        ToBeCampaign)

router = APIRouter(
    prefix="/api/v1/projects"
)

log = logging.getLogger(__name__)


# Create blank campaign for version
@router.post("/{project_name}/campaigns",
             tags=["Campaign"],
             description="Create a new campaign linked to a project-version."
                         " Multiple occurrence of the same campaign can be created",
             response_model=CampaignLight,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case),"
                                      " the version does not exist"},
                 400: {"model": ErrorMessage,
                       "description": "version already exist"},
                 401: {"model": ErrorMessage,
                       "description": "You are not authenticated"}
             }
             )
async def create_campaigns(project_name: str,
                           campaign: ToBeCampaign,
                           user: Any = Security(authorize_user, scopes=["admin"])):
    try:
        log.info("api: create_campaigns")
        return await create_campaign(project_name, campaign.version)

    except VersionNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


# Link tickets & scenarios to campaign
# { "tickets": [{"epic", "feature", "scenario_id"}...]}
@router.put("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Campaign"],)
async def fill_campaign(project_name: str,
                        version: str,
                        occurrence: str,
                        content: TicketScenarioCampaign,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    try:
        res = await db_fill_campaign(project_name, version, occurrence, content)

    except VersionNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except CampaignNotFound as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except NonUniqueError as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


# Retrieve campaign for project
@router.get("/{project_name}/campaigns",
            tags=["Campaign"],
            description="Retrieve campaign")
async def get_campaigns(project_name: str,
                        response: Response,
                        version: str = None,
                        status: CampaignStatusEnum = None,
                        limit: int = 10,
                        skip: int = 0):
    campaigns, count = await retrieve_campaign(project_name, version, status, limit=limit, skip=skip)
    response.headers["X-total-count"] = str(count)  # TODO check reason it don't work
    return campaigns


# Retrieve campaign for project-version
@router.get("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Campaign"],
            description="Retrieve the full campaign")
async def get_campaign(project_name: str,
                       version: str,
                       occurrence: str):
    return await get_campaign_content(project_name, version, occurrence)


# Retrieve scenarios for project-version-campaign-ticket
@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets",
            tags=["Campaign"],
            description="Retrieve a campaign tickets")
async def get_campaign_tickets(project_name: str,
                               version: str,
                               occurrence: str):
    try:
        return await db_get_campaign_tickets(project_name, version, occurrence)
    except CampaignNotFound as cnf:
        raise HTTPException(404, detail=" ".join(cnf.args)) from cnf


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_ref}",
            tags=["Campaign"],
            description="Retrieve a campaign ticket")
async def get_campaign_ticket(project_name: str,
                              version: str,
                              occurrence: str,
                              ticket_ref: str):
    return await db_get_campaign_ticket_scenarios(project_name, version, occurrence, ticket_ref)


@router.put("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_ref}",
            tags=["Campaign"],
            description="Add scenarios to a ticket")
async def put_campaign_ticket_scenarios(project_name: str,
                                        version: str,
                                        occurrence: str,
                                        ticket_ref: str,
                                        scenarios: List[Scenarios],
                                        user: Any = Security(authorize_user,
                                                             scopes=["admin", "user"])
                                        ):
    return await db_put_campaign_ticket_scenarios(project_name,
                                            version,
                                            occurrence,
                                            ticket_ref,
                                            scenarios)


# Retrieve scenario_internal_id for specific campaign and ticket
@router.get("/{project_name}/campaigns/{version}/{occurrence}/"
            "tickets/{reference}/scenarios/{scenario_id}",
            tags=["Campaign"])
async def get_campaign_ticket_scenario(project_name: str,
                                       version: str,
                                       occurrence: str,
                                       reference: str,
                                       scenario_id: str):
    return await db_get_campaign_ticket_scenario(project_name,
                                           version,
                                           occurrence,
                                           reference,
                                           scenario_id)


@router.put("/{project_name}/campaigns/{version}/{occurrence}/"
            "tickets/{reference}/scenarios/{scenario_id}/status",
            tags=["Campaign"])
async def update_campaign_ticket_scenario_status(project_name: str,
                                                 version: str,
                                                 occurrence: str,
                                                 reference: str,
                                                 scenario_id: str,
                                                 new_status: ScenarioStatusEnum,
                                                 user: Any = Security(authorize_user,
                                                                      scopes=["admin", "user"])):
    return await db_set_campaign_ticket_scenario_status(project_name,
                                                  version,
                                                  occurrence,
                                                  reference,
                                                  scenario_id,
                                                  new_status)
