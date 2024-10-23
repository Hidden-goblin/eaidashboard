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
    project_name: str,
    key_uuid: str,
    message: str = None,
) -> None:
    connection = redis_connection()
    data = connection.get(key_uuid)
    dict_data = RdTestResult(**json.loads(data))
    dict_data.status = "done"
    connection.set(key_uuid, json.dumps(jsonable_encoder(dict_data)))


def test_result_status(
    key_uuid: str,
) -> dict:
    connection = redis_connection()
    return json.loads(connection.get(key_uuid))
