# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from typing import Optional

from fastapi import APIRouter, File, Security, UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import MalformedCsvFile, front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.testrepository import db_project_scenarios
from app.routers.front.front_projects import repository_dropdowns
from app.routers.rest.project_repository import process_upload
from app.schema.users import User, UserLight
from app.utils.log_management import log_error
from app.utils.pages import page_numbering
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get(
    "/{project_name}/repository",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def front_project_repository(
    project_name: str,
    request: Request,
    status: Optional[str] = None,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", "") == "form":
            if user.right(project_name) == "admin":
                return templates.TemplateResponse(
                    "forms/import_repository_from_csv.html",
                    {
                        "request": request,
                        "project_name": project_name,
                    },
                )
            else:
                raise Exception("You are not authorized to access this page")

        return templates.TemplateResponse(
            "repository_board.html",
            {
                "request": request,
                "repository": {},
                "display_closed": status,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/{project_name}/repository",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def post_repository(
    project_name: str,
    request: Request,
    file: UploadFile = File(),
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        file_content = await file.read()
        try:
            await process_upload(file_content.decode(), project_name)
        except MalformedCsvFile as exp:
            message = ",".join(exp.args)
            log_error(repr(exp))
            return templates.TemplateResponse(
                "error_message.html",
                {
                    "request": request,
                    "highlight": "Error in the bulk import process ",
                    "sequel": message.replace("\n", "<br />"),
                    "advise": "Please check your file.",
                },
            )
        except Exception as exp:
            log_error(repr(exp))
            return templates.TemplateResponse(
                "error_message.html",
                {
                    "request": request,
                    "highlight": "Error in the bulk import process ",
                    "sequel": exp.args,
                    "advise": "Please check your file.",
                },
                headers={"HX-Retarget": "#messageBox"},
            )
        return templates.TemplateResponse("void.html", {"request": request})

    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/repository/epics-features",
    tags=["Front - Repository"],
    include_in_schema=False,
)
async def get_repository(
    project_name: str,
    request: Request,
    epic: str = None,
    feature: str = None,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        return await repository_dropdowns(
            project_name,
            request,
            epic,
            feature,
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{project_name}/repository/scenarios",
    tags=["Front - Repository"],
    include_in_schema=False,
)
async def get_scenario(
    project_name: str,
    request: Request,
    limit: int,
    skip: int,
    epic: Optional[str] = None,
    feature: Optional[str] = None,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        scenarios, count = await db_project_scenarios(
            project_name,
            epic,
            feature,
            limit=limit,
            offset=skip,
        )
        pages, current_page = page_numbering(
            count,
            limit=limit,
            skip=skip,
        )
        _filter = f"&epic={epic}&feature={feature}" if epic is not None and feature is not None else ""
        return templates.TemplateResponse(
            "tables/scenario_table.html",
            {
                "request": request,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "scenarios": scenarios,
                "pages": pages,
                "current_page": current_page,
                "nav_bar": count > limit,
                "filter": _filter,
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/{project_name}/repository/scenarios",
    tags=["Front - Repository"],
    include_in_schema=False,
)
async def filter_repository(
    project_name: str,
    body: dict,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        scenarios, count = await db_project_scenarios(
            project_name,
            body["epic"],
            body["feature"],
            limit=10,
        )
        pages, current_page = page_numbering(
            count,
            limit=10,
            skip=0,
        )
        return templates.TemplateResponse(
            "tables/scenario_table.html",
            {
                "request": request,
                "scenarios": scenarios,
                "pages": pages,
                "current_page": current_page,
                "nav_bar": count > 10,
                "filter": f"&epic={body['epic']}&feature=" f"{body['feature']}",
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
