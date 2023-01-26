# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import APIRouter, Form
from starlette.requests import Request

from app.conf import templates
from app.database.authorization import is_updatable
from app.database.postgre.pg_tickets_management import get_tickets_not_in_campaign
from app.database.mongo.projects import registered_projects
from app.database.postgre.testcampaign import (db_delete_campaign_ticket_scenario,
                                               db_get_campaign_ticket_scenario,
                                               db_get_campaign_ticket_scenarios,
                                               db_get_campaign_tickets,
                                               db_put_campaign_ticket_scenarios,
                                               db_set_campaign_ticket_scenario_status)
from app.database.postgre.pg_campaigns_management import create_campaign, retrieve_campaign
from app.database.postgre.testrepository import db_project_epics, db_project_features, db_project_scenarios

from app.database.utils.ticket_management import add_tickets_to_campaign
from app.schema.campaign_schema import Scenarios
from app.schema.postgres_enums import ScenarioStatusEnum
from app.utils.pages import page_numbering
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/campaigns",
            tags=["Front - Project"],
            include_in_schema=False)
async def front_project_management(project_name: str,
                                   request: Request,
                                   limit: int = 10,
                                   skip: int = 0
                                   ):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    # campaigns,  = retrieve_campaign(project_name)

    if request.headers.get("eaid-request", "") == "table":
        return await front_project_table(project_name,
                                   request,
                                   limit,
                                   skip)
    if request.headers.get("eaid-request", "") == "form":
        return front_new_campaign_form(project_name,
                                       request)
    if request.headers.get("eaid-request", "") == "REDIRECT":
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={"HX-Redirect": f"/front/v1/projects/{project_name}/campaigns"})
    projects = await registered_projects()
    return templates.TemplateResponse("campaign.html",
                                      {
                                          "request": request,
                                          "projects": projects,
                                          "campaigns": True,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name)
                                      })


async def front_project_table(project_name: str,
                              request: Request,
                              limit: int = 10,
                              skip: int = 0):

    campaigns, count = await retrieve_campaign(project_name, limit=limit, skip=skip)
    pages, current_page = page_numbering(count, limit, skip)
    return templates.TemplateResponse("tables/campaign_table.html",
                                      {
                                          "request": request,
                                          "campaigns": campaigns,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name),
                                          "pages": pages,
                                          "current": current_page,
                                          "nav_bar": count >= limit
                                      })


def front_new_campaign_form(project_name: str,
                                  request: Request):

    return templates.TemplateResponse("forms/add_campaign.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name)

                                      })

@router.post("/{project_name}/campaigns")
async def front_new_campaign(project_name: str,
                             request: Request,
                             version: str = Form(...)
                             ):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    await create_campaign(project_name, version)
    return templates.TemplateResponse("void.html",
                                      {"request": request},
                                      headers={"hx-trigger": request.headers.get("eaid-next", "")})

@router.post("/{project_name}/campaigns/scenarios",
             tags=["Front - Campaign"],
             include_in_schema=False)
async def front_scenarios_selector(project_name: str,
                                   body: dict,
                                   request: Request):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    scenarios, count = await db_project_scenarios(project_name, body["epic"], body["feature"])
    return templates.TemplateResponse("forms/add_scenarios_selector.html",
                                      {"project_name": project_name,
                                       "project_name_alias": provide(project_name),
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
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox",
                                                   "HX-Reswap": "innerHTML"})
    if request.headers.get("eaid-request", "") == "REDIRECT":
        return templates.TemplateResponse("void.html",
                                          {
                                              "request": request
                                          },
                                          headers={
                                              "HX-Redirect": f"/front/v1/projects/{project_name}"
                                                             f"/campaigns/{version}/{occurrence}"})
    campaign = await db_get_campaign_tickets(project_name, version, occurrence)
    projects = await registered_projects()
    return templates.TemplateResponse("campaign_board.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name),
                                          "version": version,
                                          "occurrence": occurrence,
                                          "campaign": campaign,
                                          "projects": projects
                                      })


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign_ticket_add_scenario(project_name: str,
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
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    epics = await db_project_epics(project_name)
    if epics:
        features = await db_project_features(project_name, epics[0])
        unique_features = {feature["name"] for feature in features}
    else:
        unique_features = set()
    return templates.TemplateResponse("forms/add_scenarios.html",
                                      {"project_name": project_name,
                                       "project_name_alias": provide(project_name),
                                       "version": version,
                                       "occurrence": occurrence,
                                       "request": request,
                                       "ticket_reference": ticket_reference,
                                       "epics": epics,
                                       "features": unique_features,
                                       "initiator": request.headers.get('eaid-next', '')})


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}/scenarios",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def front_get_campaign_ticket(project_name: str,
                                    version: str,
                                    occurrence: str,
                                    ticket_reference: str,
                                    request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    scenarios = await db_get_campaign_ticket_scenarios(project_name,
                                                 version,
                                                 occurrence,
                                                 ticket_reference)
    return templates.TemplateResponse("tables/ticket_scenarios.html",
                                      {
                                          "request": request,
                                          "project_name": project_name,
                                          "project_name_alias": provide(project_name),
                                          "version": version,
                                          "occurrence": occurrence,
                                          "ticket_reference": ticket_reference,
                                          "scenarios": scenarios,
                                          "initiator": request.headers.get('eaid-next', "")
                                      })


@router.put("/{project_name}/campaigns/{version}/{occurrence}/tickets/"
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
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    result = await db_set_campaign_ticket_scenario_status(project_name,
                                                    version,
                                                    occurrence,
                                                    ticket_reference,
                                                    scenario_id,
                                                    updated_status["new_status"])

    return templates.TemplateResponse("void.html",
                                      {"request": request},
                                      headers={"hx-trigger": request.headers.get("eaid-next", "")})


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets/"
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
    if not is_updatable(request,tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    scenario = await db_get_campaign_ticket_scenario(project_name,
                                               version,
                                               occurrence,
                                               ticket_reference,
                                               scenario_id)
    return templates.TemplateResponse("forms/campaign_scenario_status.html",
                                      {"project_name": project_name,
                                       "project_name_alias": provide(project_name),
                                       "version": version,
                                       "occurrence": occurrence,
                                       "ticket_reference": ticket_reference,
                                       "next": request.headers.get('eaid-next', ""),
                                       "scenario": scenario,
                                       "statuses": [status.value for status in ScenarioStatusEnum],
                                       "request": request})


@router.delete("/{project_name}/campaigns/{version}/{occurrence}/tickets/"
               "{ticket_reference}/scenarios/{scenario_id}",
               tags=["Front - Campaign"],
               include_in_schema=False)
async def front_delete_campaign_ticket_scenario(project_name: str,
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
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    await db_delete_campaign_ticket_scenario(project_name,
                                       version,
                                       occurrence,
                                       ticket_reference,
                                       scenario_id)
    return templates.TemplateResponse('void.html',
                                      {"request": request},
                                      headers={"HX-Trigger": request.headers.get('eaid-next', "")})


@router.put("/{project_name}/campaigns/{version}/{occurrence}/tickets/{ticket_reference}",
            tags=["Front - Campaign"],
            include_in_schema=False)
async def add_scenarios_to_ticket(project_name: str,
                                  version: str,
                                  occurrence: str,
                                  ticket_reference: str,
                                  element: dict,
                                  request: Request):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    valid = "scenario_ids" in element
    if valid and not isinstance(element["scenario_ids"], list):
        element["scenario_ids"] = [element["scenario_ids"]]

    if valid:
        await db_put_campaign_ticket_scenarios(project_name,
                                         version,
                                         occurrence,
                                         ticket_reference,
                                         [Scenarios(**element)])
    return templates.TemplateResponse('void.html',
                                      {"request": request},
                                      headers={"HX-Trigger": request.headers.get('eaid-next',"")})


@router.get("/{project_name}/campaigns/{version}/{occurrence}/tickets")
async def front_campaign_version_tickets(project_name,
                                         version,
                                         occurrence,
                                         request: Request):
    if not is_updatable(request, tuple()):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again."
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    requested = request.headers.get("eaid-request", "")
    if requested == "FORM":
        tickets = await get_tickets_not_in_campaign(project_name, version, occurrence)
        return templates.TemplateResponse("forms/link_tickets_to_campaign.html",
                                          {
                                              "request":request,
                                              "project_name": project_name,
                                              "project_name_alias": provide(project_name),
                                              "version": version,
                                              "occurrence": occurrence,
                                              "tickets": tickets
                                          })
    else:
        # TODO: return the accordion table for the campaign (ease the refresh process)
        pass

@router.post("/{project_name}/campaigns/{version}/{occurrence}/tickets")
async def front_campaign_add_tickets(project_name,
                                     version,
                                     occurrence,
                                     request: Request,
                                     body: dict):
    if not is_updatable(request, ("admin", "user")):
        return templates.TemplateResponse("error_message.html",
                                          {
                                              "request": request,
                                              "highlight": "You are not authorized",
                                              "sequel": " to perform this action.",
                                              "advise": "Try to log again"
                                          },
                                          headers={"HX-Retarget": "#messageBox"})
    await add_tickets_to_campaign(project_name, version, occurrence, body)
    return templates.TemplateResponse("error_message.html",
                                      {
                                          "request": request,
                                          "highlight": "Reload the page",
                                          "sequel": " to see your updates.",
                                          "advise": ("Reload the page as auto-reloading feature has"
                                                     " not been implemented yet.")
                                      },
                                          headers={"HX-Retarget": "#messageBox"})