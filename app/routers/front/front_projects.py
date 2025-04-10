# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import APIRouter, Security
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.pg_projects import register_project
from app.database.postgre.testrepository import db_project_epics, db_project_features
from app.schema.project_schema import RegisterProject
from app.schema.users import User, UserLight
from app.utils.log_management import log_error
from app.utils.project_alias import provide

router = APIRouter(prefix="/front/v1/projects")


@router.get(
    "",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def front_project(
    request: Request,
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    """Retrieve the create project form

    SPEC: Only application admin can create a new project
    """
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request") == "FORM":
            return templates.TemplateResponse(
                "forms/create_project.html",
                {
                    "request": request,
                    "name": None,
                    "error_message": "",
                },
            )

    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def front_create_project(
    body: RegisterProject,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    """Process create project

    SPEC: Only application admin can create project
    """
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        await register_project(body.name)
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": "modalClear",
                "HX-Trigger-After-Swap": "navRefresh",
            },
        )
    except Exception as exception:
        log_error("\n".join(exception.args))
        return templates.TemplateResponse(
            "forms/create_project.html",
            {"request": request, "name": body.name, "message": "\n".join(exception.args)},
            headers={
                "HX-Retarget": "#modal",
                "HX-Reswap": "beforeend",
            },
        )


@router.get(
    "/{project_name}",
    tags=["Front - Project"],
    include_in_schema=False,
)
async def front_project_management(
    project_name: str,
    request: Request,
    tab: str = "versions",
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    """Retrieve the project

    SPEC: Only authenticated user for the project can access
    """
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        return templates.TemplateResponse(
            "base_project.html",
            {"request": request, "tab": tab, "project_name": project_name, "project_name_alias": provide(project_name)},
            headers={
                "hx-retarget": "#content-block",
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


async def repository_dropdowns(
    project_name: str,
    request: Request,
    epic: str,
    feature: str,
) -> HTMLResponse:
    if epic is None and feature is None:
        epics = await db_project_epics(project_name)
        if epics:
            _features, _count = await db_project_features(
                project_name,
                epics[0],
            )
            # Todo: iterate to get all
            features = {feature["name"] for feature in _features[0]}
        else:
            features = set()
        return templates.TemplateResponse(
            "selectors/epic_label_selectors.html",
            {
                "request": request,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "epics": epics,
                "features": features,
            },
        )
    if epic is not None and feature is None:
        _features, count = await db_project_features(project_name, epic)
        # TODO: iterate on count
        features = {feature["name"] for feature in _features}
        return templates.TemplateResponse(
            "selectors/feature_label_selectors.html",
            {
                "request": request,
                "project_name": project_name,
                "project_name_alias": provide(project_name),
                "features": features,
            },
        )
