# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import datetime
import json
import uuid
from bson import json_util
from app.utils.project_alias import provide
from app.utils.redis import redis_connection

async def mg_insert_test_result(project_name, version, campaign_id, is_partial):
    data = {"datetime": None,
            "campaign_id": campaign_id,
            "version": version,
            "is_partial": is_partial,
            "status": "importing",
            "created": datetime.datetime.now(),
            "updated": datetime.datetime.now()}
    connection = redis_connection()
    key = f"{provide(project_name)}:{version}:{campaign_id}:{uuid.uuid4()}:result"
    connection.set(key, json.dumps(data, default=json_util.default))
    return key


async def mg_insert_test_result_done(project_name, key_uuid, message=None):
    connection = redis_connection()
    data = connection.get(key_uuid)
    dict_data = json.loads(data, object_hook=json_util.object_hook)
    dict_data["status"] = "done"
    connection.set(key_uuid, json.dumps(dict_data, default=json_util.default))

async def test_result_status(key_uuid):
    connection = redis_connection()
    return json.loads(connection.get(key_uuid))
