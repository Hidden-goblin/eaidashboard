# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from fastapi import APIRouter, File, Query, Security, UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import MalformedCsvFile, front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.test_repository.scenarios_utils import db_get_scenario_from_partial, db_update_scenario
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


@router.delete(
    "/{project_name}/repository/scenarios/{scenario_tech_id}",
    tags=["Front - Repository"],
    include_in_schema=False,
)
async def delete_scenario(
    project_name: str,
    scenario_tech_id: str,
    request: Request,
    epic_name: str,
    feature_name: str,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
    current_page: int = Query(-1),
    epic: Optional[str] = None,
    feature: Optional[str] = None,
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        current_scenario = await db_get_scenario_from_partial(
            project_name=project_name,
            epic_name=epic_name,
            feature_name=feature_name,
            scenario_tech_id=int(scenario_tech_id),
        )
        if not current_scenario:
            raise Exception(f"Scenario with tech_id {scenario_tech_id} not found.")

        await db_update_scenario(project_name, current_scenario, is_deleted=True)

        __, new_count = await db_project_scenarios(
            project_name,
            epic=epic,
            feature=feature,
            limit=1,  # Only need the count
        )
        limit = 10
        if current_page == 1:
            return await __get_scenarios(
                project_name,
                request,
                10,
                0,
                epic,
                feature,
            )
        else:
            skip = max(0, current_page - 1) * limit
            if new_count <= skip:
                skip = max(0, current_page - 2) * limit
        return await __get_scenarios(
            project_name,
            request,
            limit,
            skip,
            epic,
            feature,
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
        # TODO make a private function to call either from get_scenario or delete_scenario
        return await __get_scenarios(
            project_name,
            request,
            limit,
            skip,
            epic,
            feature,
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def __get_scenarios(
    project_name: str,
    request: Request,
    limit: int,
    skip: int,
    epic: Optional[str] = None,
    feature: Optional[str] = None,
) -> HTMLResponse:
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
        return await __get_scenarios(
            project_name,
            request,
            10,
            0,
            body["epic"],
            body["feature"],
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
