# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-


import json

from fastapi import APIRouter, Form, Security
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authentication import authenticate_user, create_access_token, invalidate_token
from app.database.authorization import front_authorize
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_versions import dashboard as db_dash
from app.schema.authentication import TokenData
from app.schema.users import User
from app.utils.log_management import log_error

router = APIRouter()


@router.get(
    "/",
    include_in_schema=False,
    tags=["Front - Dashboard"],
)
async def dashboard(
    request: Request,
    path: str = "/front/v1/dashboard",
) -> HTMLResponse:
    try:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "path": path,
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.delete(
    "/clear",
    response_class=HTMLResponse,
    tags=["Front - Utils"],
    include_in_schema=False,
)
async def return_void(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse(
        "void.html",
        {
            "request": request,
        },
        headers={
            "HX-Trigger": request.headers.get("eaid-next", ""),
        },
    )


@router.get(
    "/login",
    tags=["Front - Login"],
    include_in_schema=False,
)
async def login(
    request: Request,
) -> HTMLResponse:
    try:
        return templates.TemplateResponse(
            "forms/login_modal.html",
            {
                "request": request,
                "message": None,
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/login",
    response_class=HTMLResponse,
    tags=["Front - Login"],
    include_in_schema=False,
)
async def post_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse:
    try:
        user = authenticate_user(
            username,
            password,
        )
        if user is None:
            raise Exception("Unrecognized credentials")
        access_token = create_access_token(
            TokenData(
                sub=user.username,
                scopes=user.scopes,
            ),
        )
        # data={"sub": user.username,
        #       "scopes": user.scopes})
        request.session["token"] = access_token
        request.session["scopes"] = user.scopes
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": "modalClear",
                "HX-Trigger-After-Swap": json.dumps(
                    {
                        "navRefresh": "",
                        "update-dashboard": "",
                    },
                ),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return templates.TemplateResponse(
            "forms/login_modal.html",
            {
                "request": request,
                "message": "\n".join(exception.args),
                "username": username,
            },
            headers={
                "HX-Retarget": "#modal",
                "HX-Reswap": "beforeend",
            },
        )


@router.delete(
    "/login",
    response_class=HTMLResponse,
    tags=["Front - Login"],
    include_in_schema=False,
)
async def logout(
    request: Request,
    user: User = Security(front_authorize, scopes=["admin", "user"]),
) -> HTMLResponse:
    try:
        if isinstance(user, User):
            invalidate_token(request.session["token"])
        request.session.clear()
        return templates.TemplateResponse(
            "void.html",
            {
                "request": request,
            },
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "navRefresh": "",
                        "update-dashboard": "",
                    },
                ),
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/front/v1/navigation",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def get_navigation_bar(
    request: Request,
) -> HTMLResponse:
    projects = await registered_projects()
    is_admin = request.session.get("scopes", {}).get("*", "user") == "admin"
    user_projects = list(request.session.get("scopes", {}).keys())
    if "*" in user_projects:
        user_projects.remove("*")
    projects = projects if is_admin else list(set(user_projects).intersection(projects))
    return templates.TemplateResponse(
        "navigation.html",
        {
            "request": request,
            "projects": projects or [],
            "is_admin": is_admin,
        },
    )


@router.get(
    "/front/v1/dashboard",
    tags=["Front - Campaign"],
    include_in_schema=False,
)
async def get_dashboard(
    request: Request,
) -> HTMLResponse:
    try:
        _request = request.headers.get(
            "eaid-request",
            None,
        )
        if _request is None:
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                },
            )

        if _request == "table":
            projects, count = await db_dash()
            return templates.TemplateResponse(
                "tables/dashboard_table.html",
                {
                    "request": request,
                    "project_version": projects,
                },
            )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


# @router.get("/testResults",
#             response_class=HTMLResponse,
#             tags=["Front - Campaign"],
#             include_in_schema=False)
# async def get_test_results(request: Request):
#     try:
#         if not is_updatable(request, tuple()):
#             return templates.TemplateResponse("error_message.html",
#                                               {
#                                                   "request": request,
#                                                   "highlight": "You are not authorized",
#                                                   "sequel": " to perform this action.",
#                                                   "advise": "Try to log again."
#                                               },
#                                               headers={"HX-Retarget": "#messageBox"})
#         projects = await registered_projects()
#         result = {project: await get_project_results(project) for project in projects}
#         return templates.TemplateResponse("test_results.html",
#                                           {"request": request,
#                                            "results": result})
#     except Exception as exception:
#         log_error(repr(exception))
#         return front_error_message(templates, request, exception)
