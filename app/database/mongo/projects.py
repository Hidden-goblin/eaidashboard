# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pymongo import MongoClient

from app.app_exception import DuplicateArchivedVersion, DuplicateFutureVersion, \
    DuplicateInProgressVersion, \
    ProjectNotRegistered
from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection
from app.database.settings import registered_projects
from app.schema.project_schema import Bugs, RegisterVersion, Statistics, StatusEnum, Version


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


def create_project_version(project_name: str, project: RegisterVersion):
    if project_name not in registered_projects():
        raise ProjectNotRegistered(f"{project_name} is not a registered one."
                                   f" Please check the spelling")
    client = MongoClient(mongo_string)
    db = client[project_name]
    version = project.dict()["version"].casefold()
    # Check version is not in archived -> error
    if db[DashCollection.ARCHIVED.value].find_one({"version": version}):
        raise DuplicateArchivedVersion(f"Existing closed version of {version}")
    # Check version is not in current -> error
    if db[DashCollection.CURRENT.value].find_one({"version": version}):
        raise DuplicateInProgressVersion(f"Existing in progress version of {version}")
    # Check version is not in future -> error
    if db[DashCollection.FUTURE.value].find_one({"version": version}):
        raise DuplicateFutureVersion(f"Existing future version of {version}")

    return db[DashCollection.FUTURE.value].insert_one(Version(version=version,
                                                              created=datetime.now(),
                                                              updated=datetime.now(),
                                                              status=StatusEnum.RECORDED.value,
                                                              statistics=Statistics(open=0,
                                                                                    cancelled=0,
                                                                                    blocked=0,
                                                                                    in_progress=0,
                                                                                    done=0),
                                                              tickets=[],
                                                              bugs=Bugs()).dict())


def get_project(project_name: str, sections: Optional[List[str]]):
    client = MongoClient(mongo_string)
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    db = client[project_name]
    _sections = [sec.casefold() for sec in sections] if sections is not None else []
    result = {"name": project_name}
    if DashCollection.CURRENT.value in _sections or not _sections:
        current = db[DashCollection.CURRENT.value].find(projection={"_id": False,
                                                                    "bugs": False})
        result[DashCollection.CURRENT.value] = list(current)
    if DashCollection.FUTURE.value in _sections or not _sections:
        future = db[DashCollection.FUTURE.value].find(projection={"_id": False,
                                                                  "bugs": False})
        result[DashCollection.FUTURE.value] = list(future)
    if DashCollection.ARCHIVED.value in _sections or not _sections:
        result[DashCollection.ARCHIVED.value] = list(
            db[DashCollection.ARCHIVED.value].find(projection={"_id": False,
                                                               "bugs": False}))
    return result


def insert_results(project_name: str, result: List[dict]):
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    _result = db[DashCollection.RESULTS.value].insert_many(result)
    if not _result.acknowledged:
        raise Exception("Insertion error")
    return True


def get_project_results(project_name: str):
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    pipeline = [{"$project": {
        "myDate": {"$dateToString": {"format": "%Y%m%dT%H:%M", "date": "$date"}},
        "myStatus": "$status"
    }},
                {"$group": {
                    "_id": {"date": "$myDate", "status": "$myStatus"},
                    "mycount": {"$sum": 1}
                }},
        {"$sort": {"myDate": 1}},
        {"$group": {
            "_id": "$_id.date",
            "res": {
                "$push": {
                    "k": "$_id.status",
                    "v": "$mycount"
                }
            }
        }}
    ]
    res = db[DashCollection.RESULTS.value].aggregate(pipeline)
    result = []
    for item in list(res):
        tmp = {"date": item["_id"]}
        for sub in item["res"]:
            tmp[sub["k"]] = sub["v"]
        result.append(tmp)
    return result
    # res = db.command("aggregate", DashCollection.RESULTS.value, pipeline=pipeline, explain=True)
    # return res
