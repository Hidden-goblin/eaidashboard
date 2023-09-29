# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import APIRouter, Security
from starlette.requests import Request
from starlette.responses import HTMLResponse

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import front_authorize
from app.schema.users import User, UserLight
from app.utils.log_management import log_error

router = APIRouter(prefix="/front/v1/forms")


@router.get("/importRepository",
            tags=["Front - Repository"],
            include_in_schema=False)
async def get_import_repository_form(request: Request,
                                     user: User = Security(front_authorize, scopes=["admin", "user"])) -> HTMLResponse:
    if not isinstance(user, (User, UserLight)):
        return user
    try:
        return templates.TemplateResponse("forms/import_repository_from_csv.html",
                                          {"request": request,
                                           "project_name": request.headers.get("HX-PROJECT")})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
