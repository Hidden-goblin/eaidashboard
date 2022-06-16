# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List

from pymongo import MongoClient

from app.app_exception import VersionNotFound
from app.conf import mongo_string
from app.database.db_settings import DashCollection
from app.database.versions import get_version_and_collection
from app.schema.project_schema import Statistics, Ticket, TicketType, ToBeTicket


def update_values(project_name, project_version):
    _version, _collection = get_version_and_collection(project_name, project_version)
    client = MongoClient(mongo_string)
    db = client[project_name]
    _tickets = db[DashCollection.TICKETS.value].find({"version": _version}, {"status": True})
    stat = {}
    for _ticket in _tickets:
        if _ticket["status"] in stat:
            stat[_ticket["status"]] += 1
        else:
            stat[_ticket["status"]] = 1
    if TicketType.OPEN.value not in stat:
        stat[TicketType.OPEN.value] = 0
    if TicketType.IN_PROGRESS.value not in stat:
        stat[TicketType.IN_PROGRESS.value] = 0
    if TicketType.CANCELLED.value not in stat:
        stat[TicketType.CANCELLED.value] = 0
    if TicketType.DONE.value not in stat:
        stat[TicketType.DONE.value] = 0
    if TicketType.BLOCKED.value not in stat:
        stat[TicketType.BLOCKED.value] = 0

    db[_collection].update_one({"version": _version},
                               {"$set": {"statistics": Statistics(**stat).dict()}})


def add_ticket(project_name, project_version, ticket: ToBeTicket):
    _version, _collection = get_version_and_collection(project_name, project_version)
    if _version is None:
        raise VersionNotFound(f"Version {project_version} does not exist")
    client = MongoClient(mongo_string)
    db = client[project_name]
    return db[DashCollection.TICKETS.value].insert_one({"version": _version, **ticket.dict()})


def get_tickets(project_name, project_version):
    _version, _collection = get_version_and_collection(project_name, project_version)
    if _version is None:
        raise VersionNotFound(f"Version {project_version} does not exist")
    client = MongoClient(mongo_string)
    db = client[project_name]
    return list(db[DashCollection.TICKETS.value].find({"version": _version}, {"_id": False}))


def update_ticket(project_name, project_version, ticket_reference, updated_ticket):
    _version, _collection = get_version_and_collection(project_name, project_version)
    client = MongoClient(mongo_string)
    db = client[project_name]
    return db[DashCollection.TICKETS.value].update_one({"version": _version,
                                                        "reference": ticket_reference},
                                                       {"$push": {**updated_ticket.dict()}})
