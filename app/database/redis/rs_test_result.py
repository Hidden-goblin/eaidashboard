# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
import uuid

from fastapi.encoders import jsonable_encoder

from app.schema.redis_schema import RdTestResult
from app.utils.project_alias import provide
from app.utils.redis import redis_connection


def mg_insert_test_result(
    project_name: str,
    version: str,
    campaign_id: int,
    is_partial: bool,
) -> str:
    """
    Register a test result computation process
    Args:
        project_name: str
        version: str
        campaign_id: int, campaign internal id
        is_partial: bool, mark if the results are for specific tests (True) or whole test repository (False)

    Returns: str, project_alias:version:campaign_id:uuid:result key

    """
    data = RdTestResult(
        campaign_id=campaign_id,
        version=version,
        is_partial=is_partial,
        status="importing",
    )
    connection = redis_connection()
    key = f"{provide(project_name)}:{version}:{campaign_id}:{uuid.uuid4()}:result"
    connection.set(
        key,
        json.dumps(
            jsonable_encoder(data),
        ),
    )
    return key


def mg_insert_test_result_done(
    key_uuid: str,
    message: str = None,
) -> None:
    """
    Insert information on the result processing
    Args:
        key_uuid: str, project_alias:version:campaign_id:uuid:result key
        message: str, to optionally comment the status
    """
    connection = redis_connection()
    data = connection.get(key_uuid)
    dict_data = RdTestResult(**json.loads(data))
    dict_data.status = "done"
    if message is not None:
        dict_data.message = f"{dict_data.message}; {message}"
    connection.set(key_uuid, json.dumps(jsonable_encoder(dict_data)))


def test_result_status(
    key_uuid: str,
) -> dict:
    connection = redis_connection()
    result = connection.get(key_uuid)
    return json.loads(result) if result is not None else {}
