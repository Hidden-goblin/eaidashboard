# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime

import dpath.util
from pymongo import MongoClient
from dpath.util import merge as dp_merge

from app.app_exception import IncorrectTicketCount, ProjectNotRegistered, StatusTransitionForbidden, \
    UnknownStatusException, UpdateException
from app.conf import mongo_string
from app.database.db_settings import DashCollection
from app.database.settings import registered_projects
from app.schema.project_schema import Bugs, StatusEnum, Tickets, UpdateTickets, UpdateVersion


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
    current = db[DashCollection.CURRENT.value]
    future = db[DashCollection.FUTURE.value]
    archived = db[DashCollection.ARCHIVED.value]

    if current.find_one({"version": version.casefold()}):
        return version.casefold(), DashCollection.CURRENT.value
    if future.find_one({"version": version.casefold()}):
        return version.casefold(), DashCollection.FUTURE.value
    if archived.find_one({"version": version.casefold()}):
        return version.casefold(), DashCollection.ARCHIVED.value

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
        document["status"] = StatusEnum.ARCHIVED.value
        document["updated"] = datetime.now()
        result = db[DashCollection.ARCHIVED.value].insert_one(document)
        if not result.acknowledged:
            raise UpdateException("Cannot update the document")
        db[_collection].delete_one({"version": _version})
        return db[DashCollection.ARCHIVED.value].find_one({"version": _version},
                                                          projection={"_id": False})
    if StatusEnum(document["status"]) == StatusEnum.RECORDED:
        document["status"] = StatusEnum(to_be_status).value
        document["updated"] = datetime.now()
        result = db[DashCollection.CURRENT.value].insert_one(document)
        if not result.acknowledged:
            raise UpdateException("Cannot update the document")
        db[_collection].delete_one({"version": _version})
        return db[DashCollection.CURRENT.value].find_one({"version": _version},
                                                         projection={"_id": False})
    db = client[project_name]
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
        current = db[DashCollection.CURRENT.value].find({}, projection={"_id": False})
        future = db[DashCollection.FUTURE.value].find({}, projection={"_id": False})

        result.extend({"name": project, **cur} for cur in current)

        result.extend({"name": project, **fut} for fut in future)

    return result


def move_tickets(project_name, version, ticket_type, ticket_dispatch):
    _version = get_version(project_name, version)
    _base_type = _version["tickets"][ticket_type.value]
    to_subtract = sum(
        value for key, value in ticket_dispatch.dict().items() if key != ticket_type.value)

    if _base_type + ticket_dispatch.dict()[ticket_type.value] - to_subtract < 0:
        raise IncorrectTicketCount("Dispatch error")
    _base_tickets = Tickets(**_version["tickets"]).dict()
    for key, value in ticket_dispatch.dict().items():
        if key != ticket_type.value:
            _base_tickets[ticket_type.value] -= value
        _base_tickets[key] += value
    return update_version_data(project_name, version,
                               UpdateVersion(tickets=Tickets(**_base_tickets)))
