# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import datetime
import logging

from bson import ObjectId
from pymongo import MongoClient
from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection
from app.utils.project_alias import provide


async def mg_insert_test_result(project_name, version, campaign_id, is_partial):
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    if DashCollection.RESULTS.value not in db.list_collection_names():
        db.create_collection(DashCollection.RESULTS.value)
    collection = db.get_collection(DashCollection.RESULTS.value)
    res = collection.insert_one({"datetime": None,
                                 "campaign_id": campaign_id,
                                 "version": version,
                                 "is_partial": is_partial,
                                 "status": "importing",
                                 "created": datetime.datetime.now(),
                                 "updated": datetime.datetime.now()})
    return str(res.inserted_id)

async def mg_insert_test_result_done(project_name, uuid, message=None):
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    collection = db.get_collection(DashCollection.RESULTS.value)
    res = collection.update_one({"_id": ObjectId(uuid)}, {"$set": {"status": "available",
                                                   "updated": datetime.datetime.now()}})

    if res.modified_count != 1:
        log = logging.getLogger("uvicorn.access")
        log.error(msg=f"Cannot update the message log. {res.raw_result}")