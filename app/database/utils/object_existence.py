# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import TypeVar

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.database.postgre.pg_versions import version_exists
from app.schema.error_code import ApplicationError, ApplicationErrorCode
from app.utils.log_management import log_error
from app.utils.project_alias import provide


async def project_version_exists(
    project_name: str,
    version: str = None,
) -> ApplicationError:
    """:raise ProjectNotRegistered
    :raise VersionNotFound
    """
    if provide(project_name) is None:
        return ApplicationError(
            error=ApplicationErrorCode.project_not_registered, message=f"'{project_name}' is not registered"
        )
    if version is not None and not await version_exists(
        project_name,
        version,
    ):
        return ApplicationError(
            error=ApplicationErrorCode.version_not_found, message=f"Version '{version}' is not found"
        )


async def project_version_raise(
    project_name: str,
    version: str = None,
) -> None:
    result = await project_version_exists(
        project_name,
        version,
    )
    if result is not None:
        log_error(f"Code: {result.error}: {result.message}")
        raise HTTPException(404, result.message)


T = TypeVar("T")


def if_error_raise_http(
    result_to_test: T,
    headers: dict = None,
    to_json: bool = False,
) -> T | HTTPException | JSONResponse:
    """Return the input variable or raise HTTPException

    Returns:
        object:
    """
    if isinstance(
        result_to_test,
        ApplicationError,
    ):
        log_error(f"Code: {result_to_test.error}: {result_to_test.message}")
        match result_to_test.error.value:
            case result_to_test.error.value if result_to_test.error.value < 100:
                raise HTTPException(
                    404,
                    result_to_test.message,
                )
            case 100:
                raise HTTPException(
                    409,
                    result_to_test.message,
                )
            case result_to_test.error.value if result_to_test.error.value < 200:
                raise HTTPException(
                    400,
                    result_to_test.message,
                )
            case _:
                raise HTTPException(
                    500,
                    result_to_test.message,
                )

    if to_json:
        return JSONResponse(
            content=jsonable_encoder(result_to_test),
            headers=headers,
        )
    return result_to_test
