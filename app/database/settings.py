# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pymongo import MongoClient

from app.conf import mongo_string


def registered_projects():
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["projects"]
    cursor = collection.find()
    return [doc['name'] for doc in cursor]


def register_project(project_name: str):
    if project_name.casefold() not in registered_projects():
        client = MongoClient(mongo_string)
        db = client.settings
        collection = db.projects
        collection.insert_one({"name": project_name.casefold()})
    return project_name.casefold()
