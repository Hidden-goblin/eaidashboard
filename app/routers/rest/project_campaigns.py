# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
from datetime import datetime
from io import StringIO
from typing import Any, List, Optional, Union

from fastapi import (APIRouter,
                     File,
                     HTTPException,
                     Depends,
                     Query,
                     Response,
                     Security,
                     UploadFile)
from pymongo import MongoClient
from csv import DictReader

from starlette.background import BackgroundTasks

from app.app_exception import (CampaignNotFound, NonUniqueError, ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion, VersionNotFound)
from app.database.authorization import authorize_user
from app.database.db_settings import DashCollection
from app.database.projects import (create_project_version,
                                   get_project,
                                   get_project_results,
                                   insert_results)
from app.database.settings import registered_projects
from app.database.testcampaign import (create_campaign,
                                       db_get_campaign_ticket_scenario, db_get_campaign_tickets,
                                       db_set_campaign_ticket_scenario_status, get_campaign_content,
                                       is_campaign_exist,
                                       retrieve_campaign,
                                       fill_campaign as db_fill_campaign)
from app.database.testrepository import add_epic, add_feature, add_scenario, \
    clean_scenario_with_fake_id, db_project_epics, db_project_features, db_project_scenarios
from app.database.versions import get_version, get_version_and_collection, update_version_data, \
    update_version_status
from app.schema.postgres_enums import CampaignStatusEnum, CampaignTicketEnum, ScenarioStatusEnum
from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       TestFeature, UpdateVersion,
                                       Version,
                                       TicketProject)
from app.schema.campaign_schema import CampaignLight, TicketScenarioCampaign, ToBeCampaign
from app.conf import mongo_string
from enum import Enum

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
        _version, __ = get_version_and_collection(project_name, campaign.version)
        if _version is None:
            raise VersionNotFound(f"{campaign.version} does not belong to {project_name}.")
        return create_campaign(project_name, _version)

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
        # Check version exist
        _version, __ = get_version_and_collection(project_name, version)
        if _version is None:
            raise VersionNotFound(f"{version} does not belong to {project_name}.")
        # Check the campaign exist
        if not is_campaign_exist(project_name, version, occurrence):
            raise CampaignNotFound(f"Campaign occurrence {occurrence} "
                                   f"for project {project_name} in version {version} not found")
        res = db_fill_campaign(project_name, version, occurrence, content)

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
    campaigns, count = retrieve_campaign(project_name, version, status, limit=limit, skip=skip)
    response.headers["X-total-count"] = str(count)  # TODO check reason it don't work
    return campaigns


# Retrieve campaign for project-version
@router.get("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Campaign"], )
async def get_campaign(project_name: str,
                       version: str,
                       occurrence: str):
    return get_campaign_content(project_name, version, occurrence)


# Retrieve scenarios for project-version-campaign-ticket
@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets",
            tags=["Campaign"], )
async def get_campaign_tickets(project_name: str,
                               version: str,
                               occurrence: str,
                               fields: List[CampaignTicketEnum] = Query(default=["reference",
                                                                                 "scenario_id",
                                                                                 "status"])):
    return db_get_campaign_tickets(project_name, version, occurrence, fields)


# Retrieve scenario for specific campaign and ticket
@router.get("/{project_name}/campaigns/{version}/{occurrence}/"
            "tickets/{reference}/scenarios/{scenario_id}",
            tags=["Campaign"])
async def get_campaign_ticket_scenario(project_name: str,
                                       version: str,
                                       occurrence: str,
                                       reference: str,
                                       scenario_id: str):
    return db_get_campaign_ticket_scenario(project_name,
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
    return db_set_campaign_ticket_scenario_status(project_name,
                                                  version,
                                                  occurrence,
                                                  reference,
                                                  scenario_id,
                                                  new_status)
