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


def set_index(project_name: str):
    client = MongoClient(mongo_string)
    db = client[project_name]
    if "version" not in db["archived"].index_information():
        db["archived"].create_index("version", name="version", unique=True)
    if "version" not in db["current"].index_information():
        db["current"].create_index("version", name="version", unique=True)
    if "version" not in db["future"].index_information():
        db["future"].create_index("version", name="version", unique=True)
