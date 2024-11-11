# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging

from fastapi import APIRouter, Security
from starlette.exceptions import HTTPException

from app.database.authorization import authorize_user
from app.database.redis.rs_test_result import test_result_status
from app.schema.users import UpdateUser
from app.utils.project_alias import provide

router = APIRouter(prefix="/api/v1/status")

log = logging.getLogger(__name__)


@router.get("", description="Retrieve asynchronous status")
async def async_status(status_key: str, user: UpdateUser = Security(authorize_user, scopes=["admin", "user"])) -> dict:
    """
    Provide an endpoint to retrieve the asynchronous task status
    Validate the user is allowed and has access to the project.
    Args:
        status_key: a status key
        user: the user

    Returns: the content of the status

    """
    projects = user.scopes.keys()
    project, _ = status_key.split(":", 1)
    if user.scopes.get("*") == "admin" or any(provide(proj) == project for proj in projects):
        return test_result_status(status_key)
    else:
        raise HTTPException(403, "You cannot access this project.")
