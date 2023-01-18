# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import Any

from fastapi import (APIRouter,
                     HTTPException,
                     Response,
                     Security,
                     UploadFile,
                     File,
                     Form,
                     Header)
from fastapi.encoders import jsonable_encoder
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.app_exception import DuplicateTestResults, IncorrectFieldsRequest, MalformedCsvFile, \
    VersionNotFound
from app.database.authorization import authorize_user
from app.database.mongo.versions import get_version_and_collection
from app.database.utils.output_strategy import REGISTERED_OUTPUT
from app.database.utils.test_result_management import insert_result
from app.database.utils.what_strategy import REGISTERED_STRATEGY
from app.schema.project_schema import ErrorMessage
from app.database.postgre.pg_test_results import insert_result as pg_insert_result, TestResults
from app.schema.rest_enum import RestTestResultCategoryEnum, RestTestResultHeaderEnum, \
    RestTestResultRenderingEnum

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.post("/{project_name}/testResults",
             response_class=Response,
             status_code=204,
             description="Successful request, processing data."
                         " It might be import error during the process.\n"
                         "'campaign_occurrence' is mandatory for partial results",
             responses={
                 # 204: {"description": "Processing data"},
                 400: {"model": ErrorMessage,
                       "description": "CSV file with no headers or bad headers.\n "
                                      "Test results with same date for project/version.\n"
                                      "Missing field."},
                 404: {"model": ErrorMessage,
                       "description": "project/version not found"}
             },
             tags=["Test Results"]
             )
async def rest_import_test_results(project_name: str,
                                   background_task: BackgroundTasks,
                                   file: UploadFile = File(),
                                   version: str = Form(),
                                   result_date: datetime = Form(),
                                   is_partial: bool = Form(default=False),
                                   campaign_occurrence: str = Form(default=None),
                                   user: Any = Security(authorize_user, scopes=["admin", "user"])):
    try:
        _version, __ = await get_version_and_collection(project_name, version)
        if not _version:
            raise VersionNotFound(f"Project '{project_name}' in version '{version}' not found")
        contents = await file.read()
        decoded = contents.decode()
        res, campaign_id, rows = await insert_result(project_name,
                                                     version,
                                                     result_date,
                                                     is_partial,
                                                     decoded,
                                                     part_of_campaign_occurrence=campaign_occurrence)
        background_task.add_task(pg_insert_result,
                                  result_date,
                                  project_name,
                                  version,
                                  campaign_id,
                                  is_partial, res,
                                  rows)
        return res
    except IncorrectFieldsRequest as ifr:
        raise HTTPException(400, detail="".join(ifr.args)) from  ifr
    except DuplicateTestResults as dtr:
        raise HTTPException(400, detail=" ".join(dtr.args)) from dtr
    except MalformedCsvFile as mcf:
        raise HTTPException(400, detail=" ".join(mcf.args)) from mcf
    except VersionNotFound as vnf:
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf


@router.get("/{project_name}/testResults",
            tags=["Test Results"])
async def rest_export_results(project_name: str,
                              category: RestTestResultCategoryEnum,
                              rendering: RestTestResultRenderingEnum,
                              request: Request,
                              version: str = None,
                              campaign_occurrence: str = None,
                              accept: RestTestResultHeaderEnum = Header()
                              ):
    try:
        # TODO add triggered background task to remove old file [Trigger task]
        test_results = TestResults(REGISTERED_STRATEGY[category][rendering],
                                   REGISTERED_OUTPUT[rendering][accept])
        result = await test_results.render(project_name, version, campaign_occurrence)
        if isinstance(result, dict):
            return JSONResponse(content=jsonable_encoder(result))
        else:
            return f"{request.base_url}static/{result}"
    except VersionNotFound as vnf:
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf

