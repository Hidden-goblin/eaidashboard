# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pymongo import MongoClient

from app.app_exception import DuplicateArchivedVersion, DuplicateFutureVersion, \
    DuplicateInProgressVersion, ProjectNotRegistered
from app.conf import mongo_string
from app.database.db_settings import DashCollection
from app.database.settings import registered_projects
from app.schema.project_schema import Bugs, RegisterVersion, StatusEnum, Tickets, Version


def create_project_version(project: RegisterVersion):
    project_name = project.dict()['project'].casefold()
    if project_name not in registered_projects():
        raise ProjectNotRegistered(f"{project_name} is not a registered one."
                                   f" Please check the spelling")
    client = MongoClient(mongo_string)
    proj = project.dict()
    db = client[project_name]
    version = proj["version"].casefold()
    # Check version is not in archived -> error
    if db[DashCollection.ARCHIVED.value].find_one({"version": version}):
        raise DuplicateArchivedVersion(f"Existing closed version of {version}")
    # Check version is not in current -> error
    if db[DashCollection.CURRENT.value].find_one({"version": version}):
        raise DuplicateInProgressVersion(f"Existing in progress version of {version}")
    # Check version is not in future -> error
    if db[DashCollection.FUTURE.value].find_one({"version": proj["version"]}):
        raise DuplicateFutureVersion(f"Existing future version of {version}")

    return db[DashCollection.FUTURE.value].insert_one(Version(version=proj["version"],
                                                              created=datetime.now(),
                                                              updated=datetime.now(),
                                                              status=StatusEnum.RECORDED.value,
                                                              tickets=Tickets(open=proj["open"],
                                                                              cancelled=proj[
                                                                                  "cancelled"],
                                                                              blocked=0,
                                                                              in_progress=0,
                                                                              done=0),
                                                              bugs=Bugs()).dict())


def get_project(project_name: str, sections: Optional[List[str]]):
    client = MongoClient(mongo_string)
    if project_name not in registered_projects():
        raise ProjectNotRegistered("Project not found")
    db = client[project_name]
    _sections = [sec.casefold() for sec in sections] if sections is not None else []
    result = {"name": project_name}
    if DashCollection.CURRENT.value in _sections or not _sections:
        current = db[DashCollection.CURRENT.value].find(projection={"_id": False, "bugs": False})
        result[DashCollection.CURRENT.value] = list(current)
    if DashCollection.FUTURE.value in _sections or not _sections:
        future = db[DashCollection.FUTURE.value].find(projection={"_id": False, "bugs": False})
        result[DashCollection.FUTURE.value] = list(future)
    if DashCollection.ARCHIVED.value in _sections or not _sections:
        result[DashCollection.ARCHIVED.value] = list(
            db[DashCollection.ARCHIVED.value].find(projection={"_id": False, "bugs": False}))
    return result
