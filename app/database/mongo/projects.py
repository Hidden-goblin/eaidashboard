# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pymongo import MongoClient

from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection


def get_projects(skip:int, limit: int):
    client = MongoClient(mongo_string)
    db_names = client.list_database_names()
    db_names.pop(db_names.index("admin")) if 'admin' in db_names else None
    db_names.pop(db_names.index("config")) if 'config' in db_names else None
    db_names.pop(db_names.index("local")) if 'local' in db_names else None
    db_names.pop(db_names.index("settings")) if 'settings' in db_names else None

    db_names.sort()
    db_names = db_names[skip:limit]
    return [{"name": db_name,
             DashCollection.CURRENT.value: client[db_name][
                 DashCollection.CURRENT.value].count_documents({}),
             DashCollection.FUTURE.value: client[db_name][
                 DashCollection.FUTURE.value].count_documents({}),
             DashCollection.ARCHIVED.value: client[db_name][
                 DashCollection.ARCHIVED.value].count_documents({})}
            for db_name in db_names]