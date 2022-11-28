# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import APIRouter
from starlette.requests import Request

from app.conf import templates
from app.database.authorization import is_updatable
from app.database.settings import registered_projects
from app.database.testcampaign import (db_delete_campaign_ticket_scenario,
                                       db_get_campaign_ticket_scenario,
                                       db_get_campaign_ticket_scenarios,
                                       db_put_campaign_ticket_scenarios,
                                       db_set_campaign_ticket_scenario_status,
                                       retrieve_campaign)
from app.database.postgre.testrepository import db_project_epics, db_project_features, db_project_scenarios
from app.routers.rest.project_campaigns import get_campaign_tickets
from app.schema.campaign_schema import Scenarios
from app.schema.postgres_enums import ScenarioStatusEnum
from app.utils.pages import page_numbering

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/campaigns",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_management(project_name: str,
                                   request: Request):
    # campaigns,  = retrieve_campaign(project_name)
    projects = registered_projects()
    return templates.TemplateResponse("campaign.html",
                                      {
                                          "request": request,
                                          "projects": projects,
                                          "campaigns": True,
                                          "project_name": project_name
                                      })


@router.get("/{project_name}/campaigns/table",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_table(project_name: str,
                              request: Request,
                              limit: int = 10,
                              skip: int = 0):

    campaigns, count = retrieve_campaign(project_name, limit=limit, skip=skip)
    pages, current_page = page_numbering(count, limit, skip)
    return templates.TemplateResponse("tables/campaign_table.html",
                                      {
                                          "request": request,
                                          "campaigns": campaigns,
                                          "project_name": project_name,
                                          "pages": pages,
                                          "current": current_page,
                                          "nav_bar": count >= limit
                                      })


@router.get("/{project_name}/forms/campaign",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_new_campaign_form(project_name: str,
                                  request: Request):
    return templates.TemplateResponse("forms/add_campaign.html",
                                      {
                                          "request": request,
                                          "project_name": project_name

                                      })


@router.post("/{project_name}/campaigns/scenarios",
             tags=["Front - Campaign"],
             include_in_schema=False)
async def front_scenarios_selector(project_name: str,
                                   body: dict,
                                   request: Request):
    scenarios, count = db_project_scenarios(project_name, body["epic"], body["feature"])
    return templates.TemplateResponse("forms/add_scenarios_selector.html",
                                      {"project_name": project_name,
                                       "epic": body["epic"],
                                       "feature": body["feature"],
                                       "scenarios": scenarios,
                                       "request": request})


@router.get("/{project_name}/campaigns/{version}/{occurrence}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign(project_name: str,
                             version: str,
                             occurrence: str,
                             request: Request):
    campaign = await get_campaign_tickets(project_name, version, occurrence)
    projects = registered_projects()
    return templates.TemplateResponse("campaign_board.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "version": version,
                                          "occurrence": occurrence,
                                          "campaign": campaign,
                                          "projects": projects
                                      })


@router.get("/{project_name}/campaigns/{version}/{occurrence}/{ticket_reference}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign_ticket_update_form(project_name: str,
                                                version: str,
                                                occurrence: str,
                                                ticket_reference: str,
                                                request: Request,
                                                initiator: str = None):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          })
    epics = db_project_epics(project_name)
    features = db_project_features(project_name, epics[0])
    unique_features = {feature["name"] for feature in features}
    return templates.TemplateResponse("forms/add_scenarios.html",
                                      {"project_name": project_name,
                                       "version": version,
                                       "occurrence": occurrence,
                                       "request": request,
                                       "ticket_reference": ticket_reference,
                                       "epics": epics,
                                       "features": unique_features,
                                       "initiator": initiator})


@router.get("/{project_name}/campaigns/{version}/{occurrence}/{ticket_reference}/scenarios",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign_ticket(project_name: str,
                                    version: str,
                                    occurrence: str,
                                    ticket_reference: str,
                                    request: Request,
                                    initiator: str = None):
    scenarios = db_get_campaign_ticket_scenarios(project_name,
                                                 version,
                                                 occurrence,
                                                 ticket_reference)
    return templates.TemplateResponse("tables/ticket_scenarios.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "version": version,
                                          "occurrence": occurrence,
                                          "ticket_reference": ticket_reference,
                                          "scenarios": scenarios,
                                          "initiator": initiator
                                      })


@router.put("/{project_name}/campaigns/{version}/{occurrence}/"
            "{ticket_reference}/scenarios/{scenario_id}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_update_campaign_ticket_scenario_status(project_name: str,
                                                       version: str,
                                                       occurrence: str,
                                                       ticket_reference: str,
                                                       scenario_id: str,
                                                       updated_status: dict,
                                                       request: Request):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          })
    result = db_set_campaign_ticket_scenario_status(project_name,
                                                    version,
                                                    occurrence,
                                                    ticket_reference,
                                                    scenario_id,
                                                    updated_status["new_status"])

    return templates.TemplateResponse("error_message.html",
                                      {"request": request,
                                       "highlight": "",
                                       "sequel": "Update done",
                                       "advise": "Please reload the table to see the update."})


@router.get("/{project_name}/campaigns/{version}/{occurrence}/"
            "{ticket_reference}/scenarios/{scenario_id}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_update_campaign_ticket_scenario_update_form(project_name: str,
                                                            version: str,
                                                            occurrence: str,
                                                            ticket_reference: str,
                                                            scenario_id: str,
                                                            request: Request):
    """Admin or user can update the scenario_internal_id status"""
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          })
    scenario = db_get_campaign_ticket_scenario(project_name,
                                               version,
                                               occurrence,
                                               ticket_reference,
                                               scenario_id)
    return templates.TemplateResponse("forms/campaign_scenario_status.html",
                                      {"project_name": project_name,
                                       "version": version,
                                       "occurrence": occurrence,
                                       "ticket_reference": ticket_reference,
                                       "scenario_internal_id": scenario,
                                       "statuses": [status.value for status in ScenarioStatusEnum],
                                       "request": request})


@router.delete("/{project_name}/campaigns/{version}/{occurrence}/"
               "{ticket_reference}/scenarios/{scenario_id}",
               tags=["Front - Campaign"],
               include_in_schema=False)
async def front_delete_campaign_ticket_scenario(project_name: str,
                                                version: str,
                                                occurrence: str,
                                                ticket_reference: str,
                                                scenario_id: str,
                                                request: Request,
                                                initiator: str = None):
    """Admin or user can update the scenario_internal_id status"""
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          })
    db_delete_campaign_ticket_scenario(project_name,
                                       version,
                                       occurrence,
                                       ticket_reference,
                                       scenario_id)
    return templates.TemplateResponse('void.html',
                                      {"request": request},
                                      headers={"HX-Trigger": initiator})


@router.put("/{project_name}/campaigns/{version}/{occurrence}/"
            "{ticket_reference}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def add_scenarios_to_ticket(project_name: str,
                                  version: str,
                                  occurrence: str,
                                  ticket_reference: str,
                                  element: dict,
                                  request: Request,
                                  initiator: str = None):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          })
    valid = "scenario_ids" in element
    if valid and not isinstance(element["scenario_ids"], list):
        element["scenario_ids"] = [element["scenario_ids"]]

    if valid:
        db_put_campaign_ticket_scenarios(project_name,
                                         version,
                                         occurrence,
                                         ticket_reference,
                                         [Scenarios(**element)])
    return templates.TemplateResponse('void.html',
                                      {"request": request},
                                      headers={"HX-Trigger": initiator})
