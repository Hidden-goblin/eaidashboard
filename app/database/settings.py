# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pymongo import MongoClient

from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection


async def registered_projects():
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["projects"]
    cursor = collection.find()
    return [doc['name'] for doc in cursor]


async def register_project(project_name: str):
    if project_name.casefold() not in await registered_projects():
        client = MongoClient(mongo_string)
        db = client.settings
        collection = db.projects
        collection.insert_one({"name": project_name.casefold()})
    return project_name.casefold()


async def set_index(project_name: str):
    client = MongoClient(mongo_string)
    db = client[project_name]
    if "version" not in db[DashCollection.ARCHIVED.value].index_information():
        db[DashCollection.ARCHIVED.value].create_index("version", name="version", unique=True)
    if "version" not in db[DashCollection.CURRENT.value].index_information():
        db[DashCollection.CURRENT.value].create_index("version", name="version", unique=True)
    if "version" not in db[DashCollection.FUTURE.value].index_information():
        db[DashCollection.FUTURE.value].create_index("version", name="version", unique=True)
    if "version" not in db[DashCollection.TICKETS.value].index_information():
        db[DashCollection.TICKETS.value].create_index([("version", 1), ("reference", 1)],
                                                      name="version",
                                                      unique=True)
