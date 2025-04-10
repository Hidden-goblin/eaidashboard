# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from fastapi import APIRouter, HTTPException, Security

from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.testrepository import db_project_features
from app.database.utils.object_existence import if_error_raise_http
from app.schema.error_code import ErrorMessage
from app.schema.respository.feature_schema import Feature
from app.schema.users import UpdateUser

router = APIRouter(prefix="/api/v1/projects/{project_name}/epics/{epic_ref}/features")


@router.get(
    "/",
    response_model=List[Feature],
    responses={
        401: {"model": ErrorMessage, "description": "User is not recognized"},
        404: {"model": ErrorMessage, "description": "The project might not exist"},
        500: {"model": ErrorMessage, "description": "Server error during computation"},
    },
    tags=["Repository"],
    description="Retrieve all epics linked to the project.\n Total count in header `x-total-count`",
)
async def get_features(
    project_name: str,
    epic_ref: str,
    limit: int = 10,
    offset: int = 0,
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> List[Feature]:
    if project_name.casefold() not in await registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    try:
        epic_features, count = await db_project_features(
            project_name.casefold(),
            epic_ref,
            limit,
            offset,
        )
    except Exception as exp:
        raise HTTPException(500, repr(exp))

    return if_error_raise_http(epic_features, {"X-total-count": str(count)}, to_json=True)
