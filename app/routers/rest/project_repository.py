# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from csv import DictReader
from io import StringIO
from typing import List, Union

from fastapi import APIRouter, File, HTTPException, Security, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTasks
from starlette.responses import Response

from app.app_exception import MalformedCsvFile
from app.database.authorization import authorize_user
from app.database.postgre.pg_projects import registered_projects
from app.database.postgre.testrepository import (
    add_epic,
    add_feature,
    add_scenario,
    clean_scenario_with_fake_id,
    db_project_epics,
    db_project_features,
    db_project_scenarios,
)
from app.schema.error_code import ErrorMessage
from app.schema.postgres_enums import RepositoryEnum
from app.schema.repository_schema import Feature, Scenario, TestFeature, TestScenario
from app.schema.users import UpdateUser
from app.utils.project_alias import provide

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/epics",
            response_model=List[str],
            tags=["Repository"],
            description="Retrieve all epics linked to the project.")
async def get_epics(project_name: str,
                    user: UpdateUser = Security(
                        authorize_user, scopes=["admin", "user"])) -> List[str]:
    if project_name.casefold() not in await registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    try:
        return await db_project_epics(project_name.casefold())
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.get("/{project_name}/epics/{epic}/features",
            response_model=List[Feature],
            tags=["Repository"],
            description="Retrieve all features linked to the project for this epic")
async def get_feature(project_name: str,
                      epic: str,
                      user: UpdateUser = Security(
                          authorize_user, scopes=["admin", "user"])) -> List[Feature]:
    if project_name.casefold() not in await registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    try:
        return await db_project_features(project_name, epic)
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.get("/{project_name}/repository",
            response_model=Union[List[str], List[Feature], List[Scenario]],
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
                        feature: str = None,
                        user: UpdateUser = Security(
                            authorize_user, scopes=["admin", "user"])) -> List[str] | List[Feature] |\
                                                                          List[Scenario] | JSONResponse:
    if project_name.casefold() not in await registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    try:
        if elements == RepositoryEnum.epics:
            return await db_project_epics(project_name, limit=limit, offset=offset)
        elif elements == RepositoryEnum.features:
            if epic is not None:
                return await db_project_features(project_name, epic=epic, limit=limit,
                                                 offset=offset)
            return await db_project_features(project_name, limit=limit, offset=offset)
        else:
            temp = {"epic": epic, "feature": feature}
            result, count = await db_project_scenarios(project_name,
                                                       limit=limit,
                                                       offset=offset,
                                                       **{key: value
                                                          for key, value in temp.items() if
                                                          value is not None})
            response.headers["X-total-count"] = str(count)
            return JSONResponse(content=jsonable_encoder(result),
                                headers={"X-total-count": str(count)})
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.post("/{project_name}/repository",
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
async def upload_repository(project_name: str,  # noqa: ANN201
                            background_task: BackgroundTasks,
                            file: UploadFile = File(),
                            user: UpdateUser = Security(
                                authorize_user, scopes=["admin", "user"])):
    if project_name.casefold() not in await registered_projects():
        raise HTTPException(404, detail=f"Project '{project_name}' not found")
    try:
        contents = await file.read()
        decoded = contents.decode()
        buffer = StringIO(decoded)
        rows = DictReader(buffer)
        if all(header in rows.fieldnames for header in ("epic", "feature_filename", "feature_name",
                                                        "feature_tags", "feature_description",
                                                        "scenario_id", "scenario_name",
                                                        "scenario_tags",
                                                        "scenario_description",
                                                        "scenario_is_outline",
                                                        "scenario_steps")):
            background_task.add_task(process_upload, decoded, project_name)
            return Response(status_code=204)
        else:
            raise HTTPException(400, detail="Missing or bad csv header")
    except HTTPException as http_exception:
        raise http_exception
    except Exception as exp:
        raise HTTPException(500, repr(exp))


async def process_upload(csv_content: str, project_name: str) -> dict:
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
                 "project_name_alias": provide(project_name),
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
                          "project_name_alias": provide(project_name),
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
                  "project_name_alias": provide(project_name),
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
                           "project_name_alias": provide(project_name),
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
        await add_epic(**epic)
    for feature in features:
        await add_feature(TestFeature(**feature))
    await clean_scenario_with_fake_id(project_name.casefold())
    for scenario in scenarios:
        await add_scenario(TestScenario(**scenario))

    return {"excluded_features": excluded_features,
            "excluded_scenarios": excluded_scenarios}
