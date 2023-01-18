# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from bson import ObjectId
from pymongo import MongoClient

from app.app_exception import ProjectNotRegistered
from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection
from app.database.mongo.projects import registered_projects
from app.database.mongo.versions import get_version_and_collection, get_versions
from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.project_schema import BugsStatistics, BugTicket, Statistics, UpdateBugTicket


async def insert_bug(project_name: str, bug_ticket: BugTicket):
    version, collection = await get_version_and_collection(project_name, bug_ticket.version)
    if version is None:
        raise ProjectNotRegistered(f"Version {bug_ticket.version} not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    res = db[str(DashCollection.BUGS)].insert_one(bug_ticket.dict())
    return str(res.inserted_id)


async def get_bugs(project_name: str,
             status: Optional[BugStatusEnum] = None,
             criticality: Optional[BugCriticalityEnum] = None,
             version: str = None):
    if project_name not in await registered_projects():
        raise ProjectNotRegistered("Project not found")
    temp_request = {"status": status,
                    "criticality": criticality,
                    "version": version}
    request = {key: str(value) for key, value in temp_request.items() if value is not None}
    client = MongoClient(mongo_string)
    db = client[project_name]
    bugs = list(db[str(DashCollection.BUGS)].find(request))
    return list(map(_bugs_rewriting, bugs))


def _bugs_rewriting(bug: dict):
    return {key.replace("_id", "internal_id"): value for key, value in bug.items()}


async def db_get_bug(project_name: str,
               internal_id: str) -> dict:
    if project_name not in await registered_projects():
        raise ProjectNotRegistered("Project not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    return _bugs_rewriting(db[str(DashCollection.BUGS)].find_one({"_id": ObjectId(internal_id)}))

async def db_update_bugs(project_name, internal_id, bug_ticket: UpdateBugTicket):
    client = MongoClient(mongo_string)
    db = client[project_name]
    res0 =db[str(DashCollection.BUGS)].update_one({"_id": ObjectId(internal_id)},
                                                  {"$set": bug_ticket.to_dict()})
    res = db[str(DashCollection.BUGS)].find_one({"_id": ObjectId(internal_id)}, projection={"_id": False})
    return res


async def version_bugs(project_name, version, side_version=None):
    """Compute the total bugs in a version after a bug creation/update"""
    _version, _collection = await get_version_and_collection(project_name, version)
    client = MongoClient(mongo_string)
    db = client[project_name]
    _bugs = db[DashCollection.BUGS.value].find({"version": _version}, {"status": True,
                                                                       "criticality": True})
    stat = {}
    for _bug in _bugs:
        if f'{_bug["status"]}_{_bug["criticality"]}' in stat:
            stat[f'{_bug["status"]}_{_bug["criticality"]}'] += 1
        else:
            stat[f'{_bug["status"]}_{_bug["criticality"]}'] = 1

    db[_collection].update_one({"version": _version},
                               {"$set": {"bugs": BugsStatistics(**stat).dict()}})
    # if project_name not in await registered_projects():
    #     raise ProjectNotRegistered("Project not found")
    # client = MongoClient(mongo_string)
    # db = client[project_name]
    # pipeline_blocking = [
    #     {"$match": {"version": version, "criticality": BugCriticalityEnum.blocking}},
    #     {"$project": {"myStatus": {"$concat": ["$status", "_", BugCriticalityEnum.blocking]}}},
    #     {"$group": {
    #         "_id": "$myStatus",
    #         "count": {"$sum": 1}
    #     }},
    #     {"$replaceRoot": {"newRoot": {
    #         "$arrayToObject": [
    #             [{
    #                 "k": "$_id",
    #                 "v": "$count"
    #             }
    #             ]
    #         ]
    #     }}}
    #     ]
    # pipeline_major = [
    #     {"$match": {"version": version, "criticality": BugCriticalityEnum.major}},
    #     {"$project": {"myStatus": {"$concat": ["$status", "_", BugCriticalityEnum.major]}}},
    #     {"$group": {
    #         "_id": "$myStatus",
    #         "count": {"$sum": 1}
    #     }},
    #     {"$replaceRoot": {"newRoot": {
    #         "$arrayToObject": [
    #             [{
    #                 "k": "$_id",
    #                 "v": "$count"
    #             }
    #             ]
    #         ]
    #     }}}
    #     ]
    # pipeline_minor = [
    #     {"$match": {"version": version, "criticality": BugCriticalityEnum.minor}},
    #     {"$project": {"myStatus": {"$concat": ["$status", "_", BugCriticalityEnum.minor]}}},
    #     {"$group": {
    #         "_id": "$myStatus",
    #         "count": {"$sum": 1}
    #     }},
    #     {"$replaceRoot": {"newRoot": {
    #         "$arrayToObject": [
    #             [{
    #                 "k": "$_id",
    #                 "v": "$count"
    #             }
    #             ]
    #         ]
    #     }}}
    #     ]
    # res_blocking = db[str(DashCollection.BUGS)].aggregate(pipeline_blocking)
    # res_major = db[str(DashCollection.BUGS)].aggregate(pipeline_major)
    # res_minor = db[str(DashCollection.BUGS)].aggregate(pipeline_minor)
    # res = list(res_blocking)
    # res.extend(list(res_major))
    # res.extend(list(res_minor))
    # result = {}
    # for item in res:
    #     result = {**result,
    #               **item}
    # print(result)


async  def compute_bugs(project_name):
    # TODO: add a better AsyncGroup management
    for version in await get_versions(project_name):
        await version_bugs(project_name, version)
