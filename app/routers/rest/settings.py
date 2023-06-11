# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from fastapi import APIRouter, HTTPException, Security

from app.app_exception import DuplicateProject, ProjectNameInvalid
from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import register_project, registered_projects
from app.schema.project_schema import ErrorMessage, Project, RegisterProject
from app.schema.users import UpdateUser

router = APIRouter(
    prefix="/api/v1/settings"
)


@router.post("/projects",
             response_model=Project,
             tags=["Settings"],
             description="""Create a new project. \n project name must be strictly less than 64
             characters""",
             responses={
                 400: {"model": ErrorMessage,
                       "description": "Project name is not a valid one. More than 63 characters or"
                                      " contains / \\ $ character"},
                 401: {"model": ErrorMessage,
                       "description": "You are not authenticated"},
                 409: {"model": ErrorMessage,
                       "description": "A project with this name already exist"},
                 500: {"model": ErrorMessage,
                       "description": "Error during server computing"}
             }
             )
async def post_register_projects(project: RegisterProject,
                                 user: UpdateUser = Security(
                                     authorize_user, scopes=["admin"])) -> Project:
    try:
        _project_name = await register_project(project.dict()["name"])
        return Project(name=_project_name)
    except ProjectNameInvalid as pni:
        raise HTTPException(400, detail=" ".join(pni.args)) from pni
    except DuplicateProject as dp:
        raise HTTPException(409, detail=" ".join(dp.args)) from dp
    except Exception as exception:
        raise HTTPException(500, detail=" ".join(exception.args)) from exception


@router.get("/projects",
            response_model=List[str],
            tags=["Settings"],
            description="""Register a new project. Only admin can do so."""
            )
async def get_registered_projects() -> List[str]:
    try:
        return await registered_projects()
    except Exception as exp:
        raise HTTPException(500, repr(exp))
