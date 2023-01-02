# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime, timezone

from jwt import decode
from pymongo import MongoClient
from app.conf import mongo_string
from app import conf


def token_user(token):
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return payload.get("sub")


def token_scope(token):
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    return payload.get("scopes", [])


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
