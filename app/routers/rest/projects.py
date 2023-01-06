# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from io import StringIO
from typing import Any, List, Union

from fastapi import (APIRouter,
                     File,
                     HTTPException,
                     Query,
                     Response,
                     Security,
                     UploadFile)
from csv import DictReader

from starlette.background import BackgroundTasks

from app.app_exception import (MalformedCsvFile, ProjectNotRegistered,
                               DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion)
from app.database.authorization import authorize_user
from app.database.mongo.projects import create_project_version, get_project, get_project_results, \
    get_projects, \
    insert_results
from app.database.settings import registered_projects
from app.database.postgre.testrepository import add_epic, add_feature, add_scenario, \
    clean_scenario_with_fake_id
from app.database.mongo.versions import get_version, update_version_data, update_version_status
from app.schema.project_schema import (ErrorMessage,
                                       Project,
                                       RegisterVersion,
                                       TestFeature, TestScenario, UpdateVersion,
                                       Version,
                                       TicketProject)

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

    return await get_projects(skip, limit)


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
        return await get_project(project_name.casefold(), sections)
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
        result = await create_project_version(project_name,project)
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
        return await get_version(project_name.casefold(), version.casefold())
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
        result = await update_version_status(project_name, version, body.dict()["status"])
    # Check it's ok :/

    return await update_version_data(project_name.casefold(), version.casefold(), body)


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
    await insert_results(project_name, results)
    return {"result": "ok"}


@router.get("/projects/{project_name}/results")
async def get_results(project_name: str):
    return await get_project_results(project_name)


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
    if project_name.casefold() not in await registered_projects():
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
    """Read a csv and prepare data for insertion
    Feature without epic are removed
    Scenario in removed features are removed
    """
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    expected_header = ("epic",
                       "feature_filename",
                       "feature_name",
                       "feature_description",
                       "feature_tags",
                       "scenario_id",
                       "scenario_name",
                       "scenario_tags",
                       "scenario_description",
                       "scenario_steps")
    if any(header not in rows.fieldnames for header in expected_header):
        raise MalformedCsvFile(f"Missing header in the csv file\n\r "
                               f"Expecting: {','.join(expected_header)}\n\r"
                               f"Get only: {','.join(rows.fieldnames)}")
    # Spec: Epic has only a name and no filename
    epics = [{"project": project_name.casefold(), "epic_name": row["epic"]}
             for row in rows if not row["feature_filename"] and row["epic"]]

    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    # Spec: Feature has a filename
    # Spec: Feature must be related to an epic
    # Spec: Feature does not have steps
    features = [{"epic_name": row["epic"],
                 "feature_name": row["feature_name"],
                 "project_name": project_name,
                 "description": row["feature_description"],
                 "tags": row["feature_tags"],
                 "filename": row["feature_filename"]
                 }
                for row in rows if (not row["scenario_steps"]
                                    and row["feature_filename"]
                                    and row["epic"])]
    # Gather feature without epic
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    excluded_features = [{"epic_name": row["epic"],
                         "feature_name": row["feature_name"],
                         "project_name": project_name,
                         "description": row["feature_description"],
                         "tags": row["feature_tags"],
                         "filename": row["feature_filename"]
                         }
                        for row in rows if (not row["scenario_steps"]
                                            and row["feature_filename"]
                                            and not row["epic"])]
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    retrieved_features_filename = [item["filename"] for item in features]
    # Spec: Scenario must have scenario_step
    # Spec: Scenario must have an id
    # Spec: Scenario must in an included feature
    scenarios = [{"filename": row["feature_filename"],
                  "project_name": project_name,
                  "scenario_id": row["scenario_id"],
                  "name": row["scenario_name"],
                  "is_outline": row["scenario_is_outline"] == "True",
                  "description": row["scenario_description"],
                  "steps": row["scenario_steps"],
                  "tags": row["scenario_tags"]}
                 for row in rows if (row["scenario_steps"]
                                     and row["scenario_id"]
                                     and row[
                                         "feature_filename"] in retrieved_features_filename)]
    buffer = StringIO(csv_content, newline="")
    rows = DictReader(buffer)
    excluded_scenarios = [{"filename": row["feature_filename"],
                           "project_name": project_name,
                           "scenario_id": row["scenario_id"],
                           "name": row["scenario_name"],
                           "is_outline": row["scenario_is_outline"] == "True",
                           "description": row["scenario_description"],
                           "steps": row["scenario_steps"],
                           "tags": row["scenario_tags"]}
                          for row in rows if (row["scenario_steps"]
                                              and (not row["scenario_id"]
                                                   or row[
                                                       "feature_filename"] not in
                                                   retrieved_features_filename))]
    for epic in epics:
        add_epic(**epic)
    for feature in features:
        add_feature(TestFeature(**feature))
    clean_scenario_with_fake_id(project_name.casefold())
    for scenario in scenarios:
        add_scenario(TestScenario(**scenario))

    return {"excluded_features": excluded_features,
            "excluded_scenarios": excluded_scenarios}
