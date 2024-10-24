# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import psycopg.errors
from fastapi import APIRouter, Security
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.pg_users import create_user, get_user, get_users, update_user
from app.schema.users import UpdateUser, User, UserLight
from app.utils.log_management import log_error
from app.utils.pages import page_numbering

router = APIRouter(prefix="/front/v1/users")


@router.get(
    "/",
    tags=["Front - Users"],
    include_in_schema=False,
)
async def front_get_users(
    request: Request,
    limit: int = 10,
    skip: int = 0,
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", None) == "table":
            users, total = get_users(limit, skip)
            pages, current_page = page_numbering(total, limit, skip)
            return templates.TemplateResponse(
                "tables/users.html",
                {
                    "request": request,
                    "users": users,
                    "pages": pages,
                    "current": current_page,
                    "nav_bar": total >= limit,
                },
            )
        if request.headers.get("eaid-request", None) == "form":
            projects = await registered_projects()
            return templates.TemplateResponse(
                "forms/add_user.html",
                {"request": request, "projects": projects},
            )
        return templates.TemplateResponse(
            "base_user.html",
            {"request": request},
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.post(
    "/",
    tags=["Front - Users"],
    include_in_schema=False,
)
async def front_post_users(
    body: dict,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        _scopes = {key: "user" for key in body["user"]}
        scopes = {
            **_scopes,
            **{key: "admin" for key in body["admin"]},
            "*": "admin" if "*" in body else "user",
        }
        to_be_user = UpdateUser(
            username=body["username"],
            password=body["password"],
            scopes=scopes,
        )
        create_user(to_be_user)
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": "modalClear",  # For multiple trigger use
                # json.dumps({"triggerone":"", "triggertwo": ""})
                "HX-Trigger-After-Swap": "formDelete",
            },
        )
    except psycopg.errors.UniqueViolation:
        projects = await registered_projects()
        return templates.TemplateResponse(
            "forms/add_user.html",
            {
                "request": request,
                "projects": projects,
                "posted": body,
                "message": f"Username {body['username']} already exists.",
            },
            headers={
                "HX-Retarget": "#modal",  # Retarget
                "HX-Reswap": "beforeend",
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.get(
    "/{username}",
    tags=["Front - Users"],
    include_in_schema=False,
)
async def front_user(
    username: str,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        if request.headers.get("eaid-request", None) == "form":
            _user = get_user(username)

            projects = await registered_projects()
            return templates.TemplateResponse(
                "forms/update_user.html",
                {
                    "request": request,
                    "projects": projects,
                    "posted": _user.to_admin_user_list(),
                },
            )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)


@router.patch(
    "/{username}",
    tags=["Front - Users"],
    include_in_schema=False,
)
async def front_update_user(
    username: str,
    body: dict,
    request: Request,
    user: User = Security(front_authorize, scopes=["admin"]),
) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        _user = get_user(username)
        if _user is None:
            raise Exception("Please check the user")

        _scopes = {key: "user" for key in body["user"]}
        scopes = {
            **_scopes,
            **{key: "admin" for key in body["admin"]},
            "*": "admin" if "*" in body else "user",
        }
        to_be_user = UpdateUser(
            username=body["username"],
            password=body["password"] if body["password"] else None,
            scopes=scopes,
        )
        update_user(to_be_user)
        return templates.TemplateResponse(
            "void.html",
            {"request": request},
            headers={
                "HX-Trigger": "modalClear",  # For multiple trigger use
                # json.dumps({"triggerone":"", "triggertwo": ""})
                "HX-Trigger-After-Swap": "formDelete",
            },
        )
    except psycopg.errors.UniqueViolation:
        projects = await registered_projects()
        return templates.TemplateResponse(
            "forms/add_user.html",
            {
                "request": request,
                "projects": projects,
                "posted": body,
                "message": f"Username {body['username']} already exists.",
            },
            headers={
                "HX-Retarget": "#modal",  # Retarget
                "HX-Reswap": "beforeend",
            },
        )
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
