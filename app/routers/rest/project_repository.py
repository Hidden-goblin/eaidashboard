# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from fastapi import (APIRouter, Response)

from app.database.testrepository import db_project_epics, db_project_features, db_project_scenarios
from app.schema.postgres_enums import RepositoryEnum

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/epics",
            tags=["Repository"],
            description="Retrieve all epics linked to the project.")
async def get_epics(project_name):
    return db_project_epics(project_name.casefold())


@router.get("/{project_name}/epics/{epic}/features",
            tags=["Repository"],
            description="Retrieve all features linked to the project for this epic")
async def get_feature(project_name, epic):
    return db_project_features(project_name, epic)


@router.get("/{project_name}/repository",
            tags=["Repository"],
            description="""
            Retrieve the elements. The response depends on the retrieved elements.
            """)
async def get_scenarios(project_name: str,
                        response: Response,
                        elements: RepositoryEnum = RepositoryEnum.epics,
                        limit: int = 100,
                        offset: int = 0,
                        epic: str = None,
                        feature: str = None):
    if elements == RepositoryEnum.epics:
        return db_project_epics(project_name, limit=limit, offset=offset)
    elif elements == RepositoryEnum.features:
        if epic is not None:
            return db_project_features(project_name, epic=epic, limit=limit, offset=offset)
        return db_project_features(project_name, limit=limit, offset=offset)
    else:
        temp = {"epic": epic, "feature": feature}
        result, count = db_project_scenarios(project_name,
                                             limit=limit,
                                             offset=offset,
                                             **{key: value
                                                for key, value in temp.items() if
                                                value is not None})
        response.headers["X-total-count"] = str(count)
        return result
