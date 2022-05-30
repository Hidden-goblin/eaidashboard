# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pymongo import MongoClient
from datetime import datetime
from app.conf import mongo_string
from app.database.authentication import authenticate_user, get_password_hash


def init_user():
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]
    if "username" not in collection.index_information():
        collection.create_index("username", name="username", unique=True)

    user = collection.find_one({"username": "admin@admin.fr"})
    if not user:
        create_user("admin@admin.fr", "admin", ["admin"])


def create_user(username, password, scopes):
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]
    user = collection.insert_one({"username": username,
                                  "password": get_password_hash(password),
                                  "scopes": scopes})
    if not user.acknowledged:
        raise Exception("User not created")

    return user


def user_exist(username):
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]
    user = collection.find_one({"username": username})
    return user is not None


def self_update_user(username, password, new_password):
    user, scope = authenticate_user(username, password)
    if user is None:
        raise Exception("Unrecognized credentials")
    return update_user(username, new_password)


def update_user(username, password=None, scopes=None):
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]

    param = {"username": username,
             "password": password if password is None else get_password_hash(password),
             "scopes": scopes}

    upsert = user_exist(username)

    if not upsert and (password is None or not password):
        raise Exception("Cannot create user without password")

    to_update = {key: value for key, value in param.items() if value is not None}

    user = collection.update_one({"username": username},
                                 update={"$set": to_update}, upsert=True)
    return user.upserted_id
