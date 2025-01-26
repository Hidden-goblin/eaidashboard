# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import APIRouter, HTTPException, Security

from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.testrepository import db_scenarios
from app.database.utils.object_existence import if_error_raise_http
from app.schema.error_code import ErrorMessage
from app.schema.repository_schema import Scenarios
from app.schema.users import UpdateUser

router = APIRouter(prefix="/api/v1/projects/{project_name}/epics/{epic_ref}/features/{feature_ref}/scenarios")


@router.get(
    "/",
    response_model=Scenarios,
    tags=["Repository"],
    description="Retrieve all scenarios in a feature.",
responses={
        404: {
            "model": ErrorMessage,
            "description": "Project name is not registered (ignore case),"
            " the epic or feature does not exist",
        },
        401: {"model": ErrorMessage, "description": "You are not authenticated"},
    },
)
async def get_scenarios(
    project_name: str,
    epic_ref: str,
    feature_ref: str,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> Scenarios:
    if project_name.casefold() not in await registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    try:
        scenarios = await db_scenarios(project_name.casefold(), epic_ref, feature_ref)
    except Exception as exp:
        raise HTTPException(500, repr(exp))

    return if_error_raise_http(scenarios)
