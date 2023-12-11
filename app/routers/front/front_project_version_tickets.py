# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from logging import getLogger

from fastapi import APIRouter, Security
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.pg_tickets import get_ticket, get_tickets, update_ticket
from app.database.postgre.pg_versions import refresh_version_stats
from app.routers.front.utils import header_request
from app.schema.ticket_schema import UpdatedTicket
from app.schema.users import User, UserLight
from app.utils.project_alias import provide

logger = getLogger(__name__)
router = APIRouter(prefix="/front/v1/projects/{project_name}/versions/{version}/tickets")


@router.get("",
            tags=["Front - Tickets"],
            include_in_schema=False)
async def get_tickets_for_project_version(project_name: str,
                                          version: str,
                                          request: Request,
                                          current_user: User = Security(front_authorize)) -> HTMLResponse:
    if not isinstance(current_user, (User, UserLight)):
        return current_user
    try:
        return templates.TemplateResponse(
            "ticket_view.html",
            {
                "request": request,
                "tickets": await get_tickets(project_name, version),
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "project_version": version,
            },
        )
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)


@router.get("/{reference}",
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_ticket_edit(request: Request,
                                      project_name: str,
                                      version: str,
                                      reference: str,
                                      user: User = Security(front_authorize, scopes=["admin", "user"])) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:

        if header_request(request, "row"):
            return templates.TemplateResponse(
                "ticket_row.html",
                {
                    "request": request,
                    "ticket": await get_ticket(
                        project_name, version, reference
                    ),
                    "project_name": project_name,
                    "project_name_alias": provide(project_name),
                    "project_version": version,
                }
            )

        if header_request(request, "form"):
            return templates.TemplateResponse(
                "ticket_row_edit.html",
                {
                    "request": request,
                    "ticket": await get_ticket(
                        project_name, version, reference
                    ),
                    "project_name": project_name,
                    "project_name_alias": provide(project_name),
                    "project_version": version,
                },
            )
        raise Exception("Missing header content.")
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)


@router.put("/{reference}",
            tags=["Front - Tickets"],
            include_in_schema=False)
async def project_version_update_ticket(request: Request, project_name: str, version: str, reference: str, body: dict,
                                        background_task: BackgroundTasks,
                                        user: User = Security(front_authorize,
                                                              scopes=["admin", "user"])) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        # TODO check if a refactor might enhance readability
        res = await update_ticket(project_name,
                                  version,
                                  reference,
                                  UpdatedTicket(description=body["description"],
                                                status=body["status"]))
        if not res.acknowledged:
            logger.error("Not done")
        background_task.add_task(refresh_version_stats, project_name, version)
        return templates.TemplateResponse("ticket_row.html",
                                          {"request": request,
                                           "ticket": await get_ticket(project_name,
                                                                      version,
                                                                      reference),
                                           "project_name": project_name,
                                           "project_name_alias": provide(project_name),
                                           "project_version": version},
                                          headers={"HX-Trigger": "update-dashboard"})
    except Exception as exception:
        logger.exception(repr(exception))
        return front_error_message(templates, request, exception)
