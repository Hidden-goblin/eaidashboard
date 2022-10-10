# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
import urllib.parse

from fastapi import APIRouter
from starlette.requests import Request

from app.conf import templates
from app.database.testcampaign import retrieve_campaign
from app.utils.pages import page_numbering

router = APIRouter(prefix="/front/v1/projects")


@router.get("/{project_name}/campaigns",
            tags=["Front - Project"])
async def front_project_management(project_name: str,
                                   request: Request):
    # campaigns,  = retrieve_campaign(project_name)
    return templates.TemplateResponse("campaign.html",
                                      {
                                          "request": request,
                                          "campaigns": True,
                                          "project_name": project_name
                                      })


@router.get("/{project_name}/campaigns/table",
            tags=["Front - Project"])
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
                                          "nav_bar": count == limit
                                      })


@router.get("/{project_name}/campaigns/new_form",
            tags=["Front - Project"])
async def front_new_campaign_form(project_name: str):
    return f"{project_name}"
