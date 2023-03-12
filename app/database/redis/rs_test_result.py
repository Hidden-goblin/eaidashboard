# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import json
import uuid

from app.schema.redis_schema import RdTestResult
from fastapi.encoders import jsonable_encoder
from app.utils.project_alias import provide
from app.utils.redis import redis_connection

async def mg_insert_test_result(project_name, version, campaign_id, is_partial):
    data = RdTestResult(campaign_id=campaign_id,
                        version=version,
                        is_partial=is_partial,
                        status="importing")
    connection = redis_connection()
    key = f"{provide(project_name)}:{version}:{campaign_id}:{uuid.uuid4()}:result"
    connection.set(key, json.dumps(jsonable_encoder(data)))
    return key


async def mg_insert_test_result_done(project_name, key_uuid, message=None):
    connection = redis_connection()
    data = connection.get(key_uuid)
    dict_data = RdTestResult(**json.loads(data))
    dict_data.status = "done"
    connection.set(key_uuid, json.dumps(jsonable_encoder(dict_data)))

async def test_result_status(key_uuid):
    connection = redis_connection()
    return json.loads(connection.get(key_uuid))
