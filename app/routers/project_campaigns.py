# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
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
                                       is_campaign_exist,
                                       retrieve_campaign,
                                       fill_campaign as db_fill_campaign)
from app.database.testrepository import add_epic, add_feature, add_scenario, \
    clean_scenario_with_fake_id, db_project_epics, db_project_features, db_project_scenarios
from app.database.versions import get_version, get_version_and_collection, update_version_data, \
    update_version_status
from app.schema.postgres_enums import CampaignStatus
from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       TestFeature, TicketScenarioCampaign, ToBeCampaign,
                                       UpdateVersion,
                                       Version,
                                       TicketProject)
from app.conf import mongo_string
from enum import Enum

router = APIRouter(
    prefix="/api/v1/projects"
)


# Create blank campaign for version
@router.post("/{project_name}/campaigns",
             tags=["Campaign"],
             description="Create a new campaign linked to a project-version."
                         " Multiple occurrence of the same campaign can be created")
async def create_campaigns(project_name: str,
                           campaign: ToBeCampaign,
                           user: Any = Security(authorize_user, scopes=["admin"])):
    try:
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
                        version: str = None,
                        status: CampaignStatus = None):
    return retrieve_campaign(project_name, version, status)


@router.get("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Campaign"],)
async def get_campaign(project_name: str,
                       version: str,
                       occurrence: str):
    pass

# Retrieve campaign for project-version

# Retrieve scenarios for project-version-campaign-ticket
