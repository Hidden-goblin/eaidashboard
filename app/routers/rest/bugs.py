# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Query, Security
from psycopg.errors import UniqueViolation
from starlette.responses import Response

from app.database.authorization import authorize_user
from app.database.postgre.pg_bugs import db_get_bug, db_update_bugs, insert_bug
from app.database.postgre.pg_bugs import get_bugs as db_g_bugs
from app.database.utils.object_existence import if_error_raise_http, project_version_raise
from app.schema.bugs_schema import BugTicket, BugTicketFull, UpdateBugTicket
from app.schema.error_code import ApplicationError, ErrorMessage
from app.schema.mongo_enums import BugCriticalityEnum
from app.schema.project_schema import RegisterVersionResponse
from app.schema.status_enum import BugStatusEnum
from app.schema.users import UpdateUser
from app.utils.log_management import log_error

router = APIRouter(
    prefix="/api/v1/projects"
)


@router.get("/{project_name}/bugs",
            tags=["Bug"],
            description="Retrieve all bugs for a project no matter the versions",
            response_model=List[BugTicketFull],
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project is not found"},
                500: {"model": ErrorMessage,
                      "description": "Computation error"}
            }
            )
async def get_bugs(project_name: str,
                   response: Response,
                   version: Optional[str] = None,
                   status: Annotated[list[BugStatusEnum], Query()] = None,
                   criticality: Optional[BugCriticalityEnum] = None,
                   limit: Optional[int] = 100,
                   skip: Optional[int] = 0,
                   user: UpdateUser = Security(
                       authorize_user, scopes=["admin", "user"])
                   ) -> List[BugTicketFull]:
    await project_version_raise(project_name, version)
    try:
        result, count = await db_g_bugs(project_name=project_name,
                                        status=status,
                                        criticality=criticality,
                                        limit=limit,
                                        skip=skip,
                                        version=version)
        response.headers["X-total-count"] = str(count)
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)


@router.get("/{project_name}/bugs/{internal_id}",
            tags=["Bug"],
            description="Retrieve a bug",
            response_model=BugTicketFull,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project is not found"},
                500: {"model": ErrorMessage,
                      "description": "Computation error"}
            }
            )
async def get_bug(project_name: str,
                  internal_id: str,
                  response: Response,
                  user: UpdateUser = Security(
                      authorize_user, scopes=["admin", "user"])
                  ) -> BugTicketFull:
    await project_version_raise(project_name)
    try:
        result = await db_get_bug(project_name=project_name,
                                  internal_id=internal_id)
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)


@router.post("/{project_name}/bugs",
             response_model=RegisterVersionResponse,
             status_code=201,
             responses={
                 404: {"model": ErrorMessage,
                       "description": "Project is not found"},
                 500: {"model": ErrorMessage,
                       "description": "Computation error"}
             },
             tags=["Bug"])
async def create_bugs(project_name: str,
                      bug: BugTicket,
                      response: Response,
                      user: UpdateUser = Security(
                          authorize_user, scopes=["admin", "user"])) -> RegisterVersionResponse:
    await project_version_raise(project_name, bug.version)
    try:
        result = await insert_bug(project_name, bug)
        if not isinstance(result, ApplicationError):
            response.headers["Location"] = f"/api/v1/projects/{project_name}/bugs/{result.inserted_id}"
    except UniqueViolation as uv:
        log_error(repr(uv))
        raise HTTPException(409,
                            f"Cannot insert existing bug for '{project_name}', '{bug.version}', "
                            f"'{bug.title}'.\n"
                            f"Please check your data.") from uv
    except Exception as exp:
        log_error(" ".join(exp.args))
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)


@router.put("/{project_name}/bugs/{bug_internal_id}",
            tags=["Bug"],
            response_model=BugTicketFull,
            status_code=200,
            responses={
                404: {"model": ErrorMessage,
                      "description": "Project is not found"},
                500: {"model": ErrorMessage,
                      "description": "Computation error"}
            },
            )
async def update_bugs(project_name: str,
                      bug_internal_id: str,
                      body: UpdateBugTicket,
                      user: UpdateUser = Security(
                          authorize_user, scopes=["admin", "user"])) -> BugTicketFull:
    await project_version_raise(project_name)
    try:
        result = await db_update_bugs(project_name, bug_internal_id, body)
    except Exception as exp:
        log_error(repr(exp))
        raise HTTPException(500, " ".join(exp.args)) from exp
    return if_error_raise_http(result)
