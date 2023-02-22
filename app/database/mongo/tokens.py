# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime, timezone

from pymongo import MongoClient
from app.conf import config, mongo_string
from app.database.utils.password_management import generate_keys


def get_token_date(username):
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["token"]
    return collection.find_one({"username": username}, projection={"token_date": True})


def renew_token_date(username):
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["token"]
    return collection.update_one({"username": username},
                                 {"$set": {"token_date": datetime.now(timezone.utc)}})


def register_connection(data):
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    count =  token.count_documents({})
    token.update_one({"username": data["sub"]},
                     {"$set": {"token_date": datetime.now(timezone.utc)}},
                     upsert=True)
    return count


def renew(user):
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.update_one({"username": user},
                     {"$set": {"token_date": datetime.now(timezone.utc)}},
                     upsert=True)


def revoke(username):
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.delete_one({"username": username})


def init_user_token():
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.create_index("token_date", expireAfterSeconds=int(config["TIMEDELTA"]) * 60)
    generate_keys()
