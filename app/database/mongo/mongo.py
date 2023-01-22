# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pymongo import MongoClient

from app.conf import mongo_string
from app.utils.project_alias import register


def update_mongodb():
    client = MongoClient(mongo_string)
    db = client.settings
    collection = db.projects
    collection.update_many({"alias": {"$exists": False}},
                           [{"$set": {"alias": '$name'}}])

def mongo_register():
    client = MongoClient(mongo_string)
    db = client.settings
    collection = db.projects
    cursor = collection.find({})
    for elem in cursor:
        register(elem["name"], elem["alias"])