# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional

from pymongo import MongoClient

from app.app_exception import ProjectNotRegistered
from app.conf import mongo_string
from app.database.db_settings import DashCollection
from app.database.settings import registered_projects
from app.database.versions import get_version_and_collection
from app.schema.project_schema import BugTicket, TicketType, UpdateBugTicket


def insert_bug(project_name: str, bug_ticket: BugTicket):
    version, collection = get_version_and_collection(project_name, bug_ticket.version)
    if version is None:
        raise ProjectNotRegistered(f"Version {bug_ticket.version} not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    res = db[DashCollection.BUGS.value].insert_one(bug_ticket.dict())
    return str(res.inserted_id)


def get_bugs(project_name: str,
             status: Optional[TicketType] = None):
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    if status is not None:
        return list(db[DashCollection.BUGS.value].find({"status": status.value},
                                                       projection={"_id": False}))
    return list(db[DashCollection.BUGS.value].find(projection={"_id": False}))


def update_bugs(project_name, bug_ticket: UpdateBugTicket):
    pass


def version_bugs(project_name, version, side_version=None):
    """Compute the total bugs in a version after a bug creation/update"""
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    client = MongoClient(mongo_string)
    db = client[project_name]
    pipeline = [{"$match": {"version": version}},
                {"$project": {"myStatus": "$status"}},
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
    res = db[DashCollection.BUGS.value].aggregate(pipeline)
    result = {}
    for item in list(res):
        result = {**result,
                  **item}
    print(result)
