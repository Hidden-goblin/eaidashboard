# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pymongo import MongoClient

from app.app_exception import (DuplicateArchivedVersion,
                               DuplicateFutureVersion,
                               DuplicateInProgressVersion,
                               DuplicateProject,
                               ProjectNameInvalid,
                               ProjectNotRegistered)
from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection
from app.schema.project_schema import (RegisterVersion,
                                       Statistics)
from app.schema.status_enum import StatusEnum
from app.schema.versions_schema import Version
from app.schema.bugs_schema import Bugs
from app.utils.project_alias import (contains,
                                     provide,
                                     register)


async def get_projects(skip:int, limit: int):
    client = MongoClient(mongo_string)
    cursor = client.settings.projects.find({}, {"name":1, "_id": 0})
    db_names = client.list_database_names()
    db_names.pop(db_names.index("admin")) if 'admin' in db_names else None
    db_names.pop(db_names.index("config")) if 'config' in db_names else None
    db_names.pop(db_names.index("local")) if 'local' in db_names else None
    db_names.pop(db_names.index("settings")) if 'settings' in db_names else None

    temp_db_names = sorted([cur["name"] for cur in cursor])
    temp_db_names = temp_db_names[skip:limit]
    db_names = [{"name": name, "alias": provide(name)} for name in temp_db_names]
    return [{"name": db_name["name"],
             DashCollection.CURRENT.value: client[db_name["alias"]][
                 DashCollection.CURRENT.value].count_documents({}),
             DashCollection.FUTURE.value: client[db_name["alias"]][
                 DashCollection.FUTURE.value].count_documents({}),
             DashCollection.ARCHIVED.value: client[db_name["alias"]][
                 DashCollection.ARCHIVED.value].count_documents({})}
            for db_name in db_names]


async def create_project_version(project_name: str, project: RegisterVersion):
    if not contains(project_name):
        raise ProjectNotRegistered(f"{project_name} is not a registered one."
                                   f" Please check the spelling")
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
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


async def get_project(project_name: str, sections: Optional[List[str]]):
    client = MongoClient(mongo_string)
    if not contains(project_name):
        raise ProjectNotRegistered("Project not found")
    db = client[provide(project_name)]
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


# async def insert_results(project_name: str, result: List[dict]):
#     if project_name not in await registered_projects():
#         raise ProjectNotRegistered("Project not found")
#     client = MongoClient(mongo_string)
#     db = client[provide(project_name)]
#     _result = db[DashCollection.RESULTS.value].insert_many(result)
#     if not _result.acknowledged:
#         raise Exception("Insertion error")
#     return True


# async def get_project_results(project_name: str):
#     if project_name not in await registered_projects():
#         raise ProjectNotRegistered("Project not found")
#     client = MongoClient(mongo_string)
#     db = client[provide(project_name)]
#     pipeline = [{"$project": {
#         "myDate": {"$dateToString": {"format": "%Y%m%dT%H:%M", "date": "$date"}},
#         "myStatus": "$status"
#     }},
#                 {"$group": {
#                     "_id": {"date": "$myDate", "status": "$myStatus"},
#                     "mycount": {"$sum": 1}
#                 }},
#         {"$sort": {"myDate": 1}},
#         {"$group": {
#             "_id": "$_id.date",
#             "res": {
#                 "$push": {
#                     "k": "$_id.status",
#                     "v": "$mycount"
#                 }
#             }
#         }}
#     ]
#     res = db[DashCollection.RESULTS.value].aggregate(pipeline)
#     result = []
#     for item in list(res):
#         tmp = {"date": item["_id"]}
#         for sub in item["res"]:
#             tmp[sub["k"]] = sub["v"]
#         result.append(tmp)
#     return result
    # res = db.command("aggregate", DashCollection.RESULTS.value, pipeline=pipeline, explain=True)
    # return res


async def register_project(project_name: str):
    if len(project_name) > 63:
        raise ProjectNameInvalid("Project name must be strictly less than 64 character")
    # Add check that project name does not contain \ / $ symbols raise an error
    forbidden_char = ["\\", "/", "$"]
    if any(char in project_name for char in forbidden_char):
        raise ProjectNameInvalid("Project name must not be contains \\ / $ characters")
    if contains(project_name):
        raise DuplicateProject(f"Project name '{project_name}' "
                               f"already exists. Please update the name "
                               f"so that project can be registered.")
    register(project_name)
    client = MongoClient(mongo_string)
    db = client.settings
    collection = db.projects
    collection.insert_one({"name": project_name.casefold(),
                           "alias": provide(project_name)})
    return project_name.casefold()


async def registered_projects():
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["projects"]
    cursor = collection.find()
    return [doc['name'] for doc in cursor]


async def set_index(project_name: str):
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
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
