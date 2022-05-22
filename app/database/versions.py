# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime

import dpath.util
from pymongo import MongoClient
from dpath.util import merge as dp_merge

from app.app_exception import ProjectNotRegistered, StatusTransitionForbidden, \
    UnknownStatusException, UpdateException
from app.conf import mongo_string
from app.database.settings import registered_projects
from app.schema.project_schema import Bugs, StatusEnum, UpdateTickets, UpdateVersion


def clean_update_version(body: UpdateVersion) -> dict:
    _body = {key: value for key, value in body.dict().items() if (key in ["tickets",
                                                                          "bugs",
                                                                          "started",
                                                                          "end_forecast"] and
                                                                  value is not None)}
    if isinstance(body.tickets, UpdateTickets):
        _body["tickets"] = {key: value for key, value in body.tickets.dict().items()
                            if value is not None}
    if isinstance(body.bugs, Bugs):
        _body["bugs"] = {key: value for key, value in body.bugs.dict().items() if value is not None}

    if "started" in _body:
        _body["started"] = datetime.strptime(_body["started"], "%Y-%m-%d")
    if "end_forecast" in _body:
        _body["end_forecast"] = datetime.strptime(_body["end_forecast"], "%Y-%m-%d")
    print(_body)
    return _body


def get_version_and_collection(project_name: str, version: str):
    if project_name.casefold() not in registered_projects():
        raise ProjectNotRegistered("Project not found")

    client = MongoClient(mongo_string)
    db = client[project_name]
    current = db["current"]
    future = db["future"]
    archived = db["archived"]

    if current.find_one({"version": version.casefold()}):
        return version.casefold(), "current"
    if future.find_one({"version": version.casefold()}):
        return version.casefold(), "future"
    if archived.find_one({"version": version.casefold()}):
        return version.casefold(), "archived"

    return None, None


def get_version(project_name: str, version: str):
    _version, _collection = get_version_and_collection(project_name, version)
    if _version is None:
        return {}
    client = MongoClient(mongo_string)
    db = client[project_name]
    return db[_collection].find_one({"version": _version}, projection={"_id": False})


def update_version_status(project_name: str, version: str, to_be_status: str):
    _version, _collection = get_version_and_collection(project_name, version)
    accepted_status = [StatusEnum.RECORDED, StatusEnum.ARCHIVED, StatusEnum.CAMPAIGN_STARTED,
                       StatusEnum.CAMPAIGN_ENDED,
                       StatusEnum.TEST_PLAN_WRITING,
                       StatusEnum.TEST_PLAN_SENT,
                       StatusEnum.TEST_PLAN_ACCEPTED,
                       StatusEnum.TER_WRITING,
                       StatusEnum.TER_SENT,
                       StatusEnum.CANCELLED]
    # Check status is accepted for version
    if StatusEnum(to_be_status) not in accepted_status:
        raise UnknownStatusException("Status is not accepted")

    authorized_transition = {
        StatusEnum.RECORDED: [
            StatusEnum.TEST_PLAN_WRITING,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TEST_PLAN_WRITING: [
            StatusEnum.TEST_PLAN_SENT,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TEST_PLAN_SENT: [
            StatusEnum.TEST_PLAN_ACCEPTED,
            StatusEnum.CAMPAIGN_STARTED,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TEST_PLAN_ACCEPTED: [
            StatusEnum.CAMPAIGN_STARTED,
            StatusEnum.CANCELLED
        ],
        StatusEnum.CAMPAIGN_STARTED: [
            StatusEnum.CAMPAIGN_ENDED,
            StatusEnum.CANCELLED
        ],
        StatusEnum.CAMPAIGN_ENDED: [
            StatusEnum.TER_WRITING,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TER_WRITING: [
            StatusEnum.TER_SENT,
            StatusEnum.CANCELLED
        ],
        StatusEnum.TER_SENT: [
            StatusEnum.ARCHIVED
        ],
        StatusEnum.CANCELLED: [
            StatusEnum.ARCHIVED
        ]
    }
    # Check transition is allowed
    client = MongoClient(mongo_string)
    db = client[project_name]
    document = db[_collection].find_one({"version": _version}, projection={"_id": False})
    if StatusEnum(to_be_status) not in authorized_transition[StatusEnum(document["status"])]:
        raise StatusTransitionForbidden("Transition is not accepted")

    # Check is moving from collection?
    if StatusEnum(to_be_status) == StatusEnum.ARCHIVED:
        # Create index if not exist
        if "version" not in db["archived"].index_information():
            db["archived"].create_index("version", name="version", unique=True)
        result = db["archived"].insert_one(document)
        if not result.acknowledged:
            raise UpdateException("Cannot update the document")
        db["archived"].update_one({"version": _version},
                                  {"$set": {"status": StatusEnum.ARCHIVED.value,
                                            "updated": datetime.now()}})
        db[_collection].delete_one({"version": _version})
        return db["archived"].find_one({"version": _version}, projection={"_id": False})
    if StatusEnum(document["status"]) == StatusEnum.RECORDED:
        # Create index if not exist
        if "version" not in db["current"].index_information():
            db["current"].create_index("version", name="version", unique=True)
        result = db["current"].insert_one(document)
        if not result.acknowledged:
            raise UpdateException("Cannot update the document")
        db["current"].update_one({"version": _version},
                                 {"$set": {"status": StatusEnum(to_be_status).value,
                                           "updated": datetime.now()}})
        db[_collection].delete_one({"version": _version})
        return db["current"].find_one({"version": _version}, projection={"_id": False})

    db[_collection].update_one({"version": _version},
                               {"$set": {"status": StatusEnum(to_be_status).value,
                                         "updated": datetime.now()}})
    return db[_collection].find_one({"version": _version}, projection={"_id": False})


def update_version_data(project_name: str, version: str, body: UpdateVersion):
    _version, _collection = get_version_and_collection(project_name, version)
    client = MongoClient(mongo_string)
    db = client[project_name]
    document = db[_collection].find_one({"version": _version}, projection={"_id": False,
                                                                           "created": False,
                                                                           "updated": False,
                                                                           "version": False,
                                                                           "status": False})
    document = dp_merge(document, clean_update_version(body), flags=dpath.util.MERGE_REPLACE)
    result = db[_collection].update_one({"version": _version},
                                        {"$set": {**document,
                                                  "updated": datetime.now()}})
    if not result.acknowledged:
        raise UpdateException("Update date didn't work")

    return db[_collection].find_one({"version": _version}, projection={"_id": False})


def dashboard():
    projects = registered_projects()
    client = MongoClient(mongo_string)
    result = []
    for project in projects:
        db = client[project]
        current = db["current"].find({}, projection={"_id": False})
        future = db["future"].find({}, projection={"_id": False})

        result.extend({"name": project, **cur} for cur in current)

        result.extend({"name": project, **fut} for fut in future)

    return result
