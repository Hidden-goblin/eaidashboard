# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import List, Union

from pymongo import MongoClient

from app.app_exception import VersionNotFound
from app.conf import mongo_string
from app.database.mongo.db_settings import DashCollection
from app.database.mongo.versions import get_version_and_collection
from app.schema.project_schema import Statistics, TicketType
from app.schema.ticket_schema import Ticket, ToBeTicket, UpdatedTicket
from app.utils.project_alias import provide


async def update_values(project_name, project_version):
    _version, _collection = await get_version_and_collection(project_name, project_version)
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
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


async def add_ticket(project_name, project_version, ticket: ToBeTicket):
    _version, _collection = await get_version_and_collection(project_name, project_version)
    if _version is None:
        raise VersionNotFound(f"Version {project_version} does not exist")
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    return db[DashCollection.TICKETS.value].insert_one({"version": _version, **ticket.dict()})


async def get_tickets(project_name, project_version) -> List[Ticket]:
    _version, _collection = await get_version_and_collection(project_name, project_version)
    if _version is None:
        raise VersionNotFound(f"Version {project_version} does not exist")
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    return [Ticket(**_ticket) for _ticket in db[DashCollection.TICKETS.value].find(
        {"version": _version}, {"_id": False})]


async def update_ticket(project_name: str,
                  project_version: str,
                  ticket_reference: str,
                  updated_ticket: UpdatedTicket):
    _to_update = await get_ticket(project_name, project_version, ticket_reference)
    if _to_update is None:
        raise VersionNotFound(f"Ticket {ticket_reference} in "
                              f"version {project_version} does not exist")
    _updated_ticket = updated_ticket.dict()
    _to_update["updated"] = _updated_ticket["updated"]
    if "version" in _updated_ticket and _updated_ticket["version"] is not None:
        _version, _collection = await get_version_and_collection(project_name, _updated_ticket["version"])
        if _version is None:
            raise VersionNotFound(f"Destination version {_version} does not exist")
        _to_update["version"] = _version
    if "status" in _updated_ticket and _updated_ticket["status"] is not None:
        _status = TicketType(_updated_ticket["status"])
        _to_update["status"] = _status.value
    if "description" in _updated_ticket and _updated_ticket["description"] is not None:
        _to_update["description"] = _updated_ticket["description"]
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    db[DashCollection.TICKETS.value].delete_one({"version": project_version,
                                                 "reference": ticket_reference})

    return db[DashCollection.TICKETS.value].insert_one(_to_update)


async def get_ticket(project_name, project_version, reference):
    _version, _collection = await get_version_and_collection(project_name, project_version)
    if _version is None:
        raise VersionNotFound(f"Version {project_version} does not exist")
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    return db[DashCollection.TICKETS.value].find_one({"version": _version,
                                                      "reference": reference}, {"_id": False})


async def get_tickets_by_reference(project_name: str, project_version: str, references: Union[List, set]):
    _version, _collection = await get_version_and_collection(project_name, project_version)
    if _version is None:
        raise VersionNotFound(f"Version {project_version} does not exist")
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    return db[DashCollection.TICKETS.value].find({"reference": {"$in": list(references)},
                                                  "version": _version},
                                                 {"_id": False})