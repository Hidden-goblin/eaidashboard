# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import datetime
from typing import List, Optional

from pymongo import MongoClient

from app.app_exception import DuplicateArchivedVersion, DuplicateFutureVersion, \
    DuplicateInProgressVersion, ProjectNotRegistered
from app.conf import mongo_string
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
    if db["archived"].find_one({"version": version}):
        raise DuplicateArchivedVersion(f"Existing closed version of {version}")
    # Check version is not in current -> error
    if db["current"].find_one({"version": version}):
        raise DuplicateInProgressVersion(f"Existing in progress version of {version}")
    # Check version is not in future -> error
    if db["future"].find_one({"version": proj["version"]}):
        raise DuplicateFutureVersion(f"Existing future version of {version}")

    # Create index if not exist
    if "version" not in db["future"].index_information():
        db["future"].create_index("version", name="version", unique=True)

    return db["future"].insert_one(Version(version=proj["version"],
                                           created=datetime.now(),
                                           updated=datetime.now(),
                                           status=StatusEnum.RECORDED.value,
                                           tickets=Tickets(open=proj["open"],
                                                           cancelled=proj["cancelled"],
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
    if "current" in _sections or not _sections:
        current = db["current"].find(projection={"_id": False, "bugs": False})
        result["current"] = list(current)
    if "future" in _sections or not _sections:
        future = db["future"].find(projection={"_id": False, "bugs": False})
        result["future"] = list(future)
    if "archived" in _sections or not _sections:
        archived = db["current"].find(projection={"_id": False, "bugs": False})
        result["archived"] = list(archived)
    return result
