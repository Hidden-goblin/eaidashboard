# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from io import StringIO
from typing import Any, List, Optional, Union

from fastapi import (APIRouter,
                     File,
                     HTTPException,
                     Depends,
                     Query,
                     Response,
                     Security,
                     UploadFile)
from pymongo import MongoClient
from csv import DictReader

from starlette.background import BackgroundTasks

from app.app_exception import (ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion)
from app.database.authorization import authorize_user
from app.database.db_settings import DashCollection
from app.database.projects import (create_project_version,
                                   get_project,
                                   get_project_results,
                                   insert_results)
from app.database.settings import registered_projects
from app.database.testrepository import add_epic, add_feature, add_scenario, \
    clean_scenario_with_fake_id
from app.database.versions import get_version, update_version_data, update_version_status
from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       TestFeature, UpdateVersion,
                                       Version,
                                       TicketProject)
from app.conf import mongo_string

router = APIRouter(
    prefix="/api/v1"
)


@router.get("/projects",
            response_model=List[Project],
            tags=["Projects"],
            description="Retrieve all projects")
async def projects(response: Response,
                   skip: int = 0,
                   limit: int = 100):
    client = MongoClient(mongo_string)
    db_names = client.list_database_names()
    db_names.pop(db_names.index("admin")) if 'admin' in db_names else None
    db_names.pop(db_names.index("config")) if 'config' in db_names else None
    db_names.pop(db_names.index("local")) if 'local' in db_names else None
    db_names.pop(db_names.index("settings")) if 'settings' in db_names else None

    db_names.sort()
    db_names = db_names[skip:limit]
    return [{"name": db_name,
             DashCollection.CURRENT.value: client[db_name][
                 DashCollection.CURRENT.value].count_documents({}),
             DashCollection.FUTURE.value: client[db_name][
                 DashCollection.FUTURE.value].count_documents({}),
             DashCollection.ARCHIVED.value: client[db_name][
                 DashCollection.ARCHIVED.value].count_documents({})}
            for db_name in db_names]


@router.get("/projects/{project_name}",
            response_model=TicketProject,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Projects"],
            description="""Retrieve one specific project details.

**sections** has value in

  - future
  - archived
  - current
            
denoting the project's version you want to retrieve.
            """
            )
async def one_project(project_name: str,
                      sections: Union[List[str], None] = Query(default=None)):
    try:
        return get_project(project_name.casefold(), sections)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


@router.post("/projects/{project_name}/versions",
             response_model=str,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project name is not registered (ignore case)"},
                 400: {"model": ErrorMessage,
                       "description": "version already exist"}
             },
             tags=["Projects"],
             description="""Create a new version of this project
Only admin can create new version.""")
async def post_projects(project_name: str,
                        project: RegisterVersion,
                        user: Any = Security(authorize_user, scopes=["admin"])):
    try:
        result = create_project_version(project_name,project)
        return str(result.inserted_id)
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr
    except DuplicateArchivedVersion as dav:
        raise HTTPException(400, detail=" ".join(dav.args)) from dav
    except DuplicateFutureVersion as dfv:
        raise HTTPException(400, detail=" ".join(dfv.args)) from dfv
    except DuplicateInProgressVersion as dipv:
        raise HTTPException(400, detail=" ".join(dipv.args)) from dipv


@router.get("/projects/{project_name}/versions/{version}",
            response_model=Union[Version, dict],
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description="Retrieve a specific project's version details")
async def version_details(project_name: str,
                          version: str):
    try:
        return get_version(project_name.casefold(), version.casefold())
    except ProjectNotRegistered as pnr:
        raise HTTPException(404, detail=" ".join(pnr.args)) from pnr


@router.put("/projects/{project_name}/versions/{version}",
            response_model=Version,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project name is not registered (ignore case)"}
            },
            tags=["Versions"],
            description="""Update the project-version on status, issues and bugs.
            
**started** and **end_forecast** are dates in YYY-mm-dd format.
            
**status** is one of:

   - in progress
   - recorded
   - campaign started
   - campaign ended
   - test plan writing
   - test plan sent
   - test plan accepted
   - ter writing
   - ter sent
   - cancelled 
   - archived
            
Only admin or user can update a version"""
            )
async def update_version(project_name: str,
                         version: str,
                         body: UpdateVersion,
                         user: Any = Security(authorize_user, scopes=["admin", "user"])):
    result = None
    if "status" in body.dict() and body.dict()["status"] is not None:
        result = update_version_status(project_name, version, body.dict()["status"])
    # Check it's ok :/

    return update_version_data(project_name.casefold(), version.casefold(), body)


@router.post("/projects/{project_name}/results")
async def upload_results(project_name: str,
                         result_date: str,
                         file: UploadFile = File(),
                         user: Any = Security(authorize_user, scopes=["admin", "user"])
                         ):
    contents = await file.read()
    decoded = contents.decode()
    buffer = StringIO(decoded)
    rows = DictReader(buffer)
    results = [{**row, "date": datetime.strptime(result_date, "%Y%m%dT%H:%M")} for row in rows]
    insert_results(project_name, results)
    return {"result": "ok"}


@router.get("/projects/{project_name}/results")
async def get_results(project_name: str):
    return get_project_results(project_name)


@router.post("/projects/{project_name}/repository",
             response_class=Response,
             status_code=204,
             description="Successful request, processing data."
                         " It might be import error during the process.",
             responses={
                 # 204: {"description": "Processing data"},
                 400: {"model": ErrorMessage,
                       "description": "CSV file with no headers or bad headers"},
                 404: {"model": ErrorMessage,
                       "description": "project not found"}
             },
             tags=["Repository"])
async def upload_repository(project_name: str,
                            background_task: BackgroundTasks,
                            file: UploadFile = File(),
                            user: Any = Security(authorize_user, scopes=["admin", "user"])):
    if project_name.casefold() not in registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    contents = await file.read()
    decoded = contents.decode()
    buffer = StringIO(decoded)
    rows = DictReader(buffer)
    if all(header in rows.fieldnames for header in ("epic", "feature_filename", "feature_name",
                                                    "feature_tags", "feature_description",
                                                    "scenario_id", "scenario_name","scenario_tags",
                                                    "scenario_description", "scenario_is_outline",
                                                    "scenario_steps")):
        background_task.add_task(process_upload, decoded, project_name)
        return Response(status_code=204)
    else:
        raise HTTPException(400, detail="Missing or bad csv header")


def process_upload(csv_content, project_name):
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    epics = [{"project": project_name.casefold(), "epic_name": row["epic"]}
             for row in rows if not row["feature_filename"] and row["epic"]]
    epics.append({"project": project_name, "epic_name": "XXX-application-undefined-epic"})
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    features = [{"epic_name": row["epic"] or "XXX-application-undefined-epic",
                 "feature_name": row["feature_name"],
                 "project_name": project_name,
                 "description": row["feature_description"],
                 "tags": row["feature_tags"],
                 "filename": row["feature_filename"]
                 }
                for row in rows if not row["scenario_steps"] and row["feature_filename"]]
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    scenarios = [{"filename": row["feature_filename"],
                  "project_name": project_name,
                  "scenario_id": row["scenario_id"],
                  "name": row["scenario_name"],
                  "is_outline": row["scenario_is_outline"] == "True",
                  "description": row["scenario_description"],
                  "steps": row["scenario_steps"],
                  "tags": row["scenario_tags"]} for row in rows if row["scenario_steps"]]
    for epic in epics:
        add_epic(**epic)
    for feature in features:
        add_feature(feature)
    clean_scenario_with_fake_id(project_name.casefold())
    for index, scenario in enumerate(scenarios):
        if not scenario["scenario_id"]:
            scenario["scenario_id"] = f"XXX-application-undefined-id-{index}"
        add_scenario(scenario)
