# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from pymongo import MongoClient

from app.app_exception import ProjectNotRegistered
from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection
from app.database.settings import registered_projects
from app.database.versions import get_version_and_collection, get_versions
from app.schema.mongo_enums import BugCriticalityEnum, BugStatusEnum
from app.schema.project_schema import BugTicket, UpdateBugTicket


def insert_bug(project_name: str, bug_ticket: BugTicket):
    version, collection = get_version_and_collection(project_name, bug_ticket.version)
    if version is None:
        raise ProjectNotRegistered(f"Version {bug_ticket.version} not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    res = db[DashCollection.BUGS.value].insert_one(bug_ticket.dict())
    return str(res.inserted_id)


def get_bugs(project_name: str,
             status: Optional[BugStatusEnum] = None,
             criticality: Optional[BugCriticalityEnum] = None,
             version: str = None):
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    temp_request = {"status": status,
                    "criticality": criticality,
                    "version": version}
    request = {key: value for key, value in temp_request.items() if value is not None}
    client = MongoClient(mongo_string)
    db = client[project_name]
    return list(db[DashCollection.BUGS.value].find(request, projection={"_id": False}))


def update_bugs(project_name, bug_ticket: UpdateBugTicket):
    pass


def version_bugs(project_name, version, side_version=None):
    """Compute the total bugs in a version after a bug creation/update"""
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    pipeline_blocking = [{"$match": {"version": version, "criticality": BugCriticalityEnum.blocking}},
                {"$project": {"myStatus": {"$concat": ["$status", "_", BugCriticalityEnum.blocking]}}},
                {"$group": {
                    "_id": "$myStatus",
                    "count": {"$sum": 1}
                }},
                {"$replaceRoot": {"newRoot": {
                    "$arrayToObject": [
                        [{
                            "k": "$_id",
                            "v": "$count"
                        }
                        ]
                    ]
                }}}
                ]
    pipeline_major = [{"$match": {"version": version, "criticality": BugCriticalityEnum.major}},
                {"$project": {"myStatus": {"$concat": ["$status", "_", BugCriticalityEnum.major]}}},
                {"$group": {
                    "_id": "$myStatus",
                    "count": {"$sum": 1}
                }},
                {"$replaceRoot": {"newRoot": {
                    "$arrayToObject": [
                        [{
                            "k": "$_id",
                            "v": "$count"
                        }
                        ]
                    ]
                }}}
                ]
    pipeline_minor = [{"$match": {"version": version, "criticality": BugCriticalityEnum.minor}},
                {"$project": {"myStatus": {"$concat": ["$status", "_", BugCriticalityEnum.minor]}}},
                {"$group": {
                    "_id": "$myStatus",
                    "count": {"$sum": 1}
                }},
                {"$replaceRoot": {"newRoot": {
                    "$arrayToObject": [
                        [{
                            "k": "$_id",
                            "v": "$count"
                        }
                        ]
                    ]
                }}}
                ]
    res_blocking = db[DashCollection.BUGS.value].aggregate(pipeline_blocking)
    res_major = db[DashCollection.BUGS.value].aggregate(pipeline_major)
    res_minor = db[DashCollection.BUGS.value].aggregate(pipeline_minor)
    res = list(res_blocking)
    res.extend(list(res_major))
    res.extend(list(res_minor))
    result = {}
    for item in res:
        result = {**result,
                  **item}
    print(result)


def compute_bugs(project_name):
    for version in get_versions(project_name):
        version_bugs(project_name, version)
