# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter
from starlette.requests import Request

from app.app_exception import front_error_message
from app.conf import templates
from app.database.authorization import is_updatable
from app.utils.log_management import log_error

router = APIRouter(prefix="/front/v1/forms")


@router.get("/importRepository",
            tags=["Front - Repository"],
            include_in_schema=False)
async def get_import_repository_form(request: Request):
    try:
        if is_updatable(request, ("admin", "user")):
            return templates.TemplateResponse("forms/import_repository_from_csv.html",
                                              {"request": request,
                                               "project_name": request.headers.get("HX-PROJECT")})
        else:
            return templates.TemplateResponse("error_message.html",
                                              {
                                                  "request": request,
                                                  "highlight": "You are not authorized",
                                                  "sequel": " to perform this action.",
                                                  "advise": "Try to log again"
                                              },
                                              headers={"HX-Retarget": "#messageBox"})
    except Exception as exception:
        log_error(repr(exception))
        return front_error_message(templates, request, exception)
