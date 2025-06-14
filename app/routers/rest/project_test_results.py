# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime

from fastapi import APIRouter, File, Form, Header, HTTPException, Security, UploadFile
from fastapi.encoders import jsonable_encoder
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.app_exception import DuplicateTestResults, IncorrectFieldsRequest, MalformedCsvFile, VersionNotFound
from app.database.authorization import authorize_user
from app.database.postgre.pg_test_results import TestResults
from app.database.postgre.pg_test_results import insert_result as pg_insert_result
from app.database.postgre.pg_versions import version_exists
from app.database.redis.rs_file_management import rs_invalidate_file, rs_record_file, rs_retrieve_file
from app.database.utils.output_strategy import REGISTERED_OUTPUT
from app.database.utils.test_result_management import insert_result
from app.database.utils.what_strategy import REGISTERED_STRATEGY
from app.schema.error_code import ErrorMessage
from app.schema.rest_enum import RestTestResultCategoryEnum, RestTestResultHeaderEnum, RestTestResultRenderingEnum
from app.schema.users import UpdateUser
from app.utils.project_alias import provide

router = APIRouter(prefix="/api/v1/projects")


@router.post(
    "/{project_name}/testResults",
    status_code=200,
    description="Successful request, processing data."
    " It might be import error during the process.\n"
    "'campaign_occurrence' is mandatory for partial results",
    responses={
        # 204: {"description": "Processing data"},
        400: {
            "model": ErrorMessage,
            "description": "CSV file with no headers or bad headers.\n "
            "Test results with same date for project/version.\n"
            "Missing field.",
        },
        404: {"model": ErrorMessage, "description": "project/version not found"},
    },
    tags=["Test Results"],
)
async def rest_import_test_results(
    project_name: str,
    background_task: BackgroundTasks,
    file: UploadFile = File(),
    version: str = Form(),
    result_date: datetime = Form(),
    is_partial: bool = Form(default=False),
    campaign_occurrence: str = Form(default=None),
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
) -> str:
    try:
        if not version_exists(
            project_name,
            version,
        ):
            raise VersionNotFound(f"Project '{project_name}' in version '{version}' not found")
        contents = await file.read()
        decoded = contents.decode()
        res, campaign_id, rows = await insert_result(
            project_name,
            version,
            result_date,
            is_partial,
            decoded,
            part_of_campaign_occurrence=campaign_occurrence,
        )
        background_task.add_task(
            pg_insert_result,
            result_date,
            project_name,
            version,
            campaign_id,
            is_partial,
            res,
            rows,
        )
        # Invalidate current result files and remove them
        if campaign_occurrence is None:
            rs_invalidate_file(f"file:{provide(project_name)}:{version}:*")
        else:
            rs_invalidate_file(f"file:{provide(project_name)}:{version}:{campaign_occurrence}:*")
        return res
    except IncorrectFieldsRequest as ifr:
        raise HTTPException(400, detail="".join(ifr.args)) from ifr
    except DuplicateTestResults as dtr:
        raise HTTPException(400, detail=" ".join(dtr.args)) from dtr
    except MalformedCsvFile as mcf:
        raise HTTPException(400, detail=" ".join(mcf.args)) from mcf
    except VersionNotFound as vnf:
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf
    except Exception as exp:
        raise HTTPException(500, repr(exp))


@router.get(
    "/{project_name}/testResults",
    description="""Provide test results for a project.

            **Partial test repository result** can be retrieved when providing a campaign
            execution (version and occurrence).

            **Complete test repository results** are retrieved on the all other cases.

            Please note that partial results are not counted in the application results.
            """,
    tags=["Test Results"],
)
async def rest_export_results(  # noqa:ANN201
    project_name: str,
    category: RestTestResultCategoryEnum,
    rendering: RestTestResultRenderingEnum,
    request: Request,
    version: str = None,
    campaign_occurrence: str = None,
    accept: RestTestResultHeaderEnum = Header(),
    user: UpdateUser = Security(authorize_user, scopes=["admin", "user"]),
):
    try:
        file_key = f"file:{provide(project_name)}:{version}:{campaign_occurrence}:{category}:{rendering}:{accept}"
        if accept != "application/json":
            filename = rs_retrieve_file(file_key)
            if filename is not None:
                return f"{request.base_url}static/{filename}"
        test_results = TestResults(
            REGISTERED_STRATEGY[category][rendering],
            REGISTERED_OUTPUT[rendering][accept],
        )
        result = await test_results.render(
            project_name,
            version,
            campaign_occurrence,
        )

        if isinstance(result, dict):
            return JSONResponse(content=jsonable_encoder(result))

        rs_record_file(file_key, result)
        return f"{request.base_url}static/{result}"
    except VersionNotFound as vnf:
        raise HTTPException(404, detail=" ".join(vnf.args)) from vnf
    except Exception as exp:
        raise HTTPException(500, repr(exp)) from exp
