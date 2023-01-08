# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from psycopg.rows import dict_row, tuple_row

from app.app_exception import VersionNotFound
from app.database.mongo.versions import get_version_and_collection
from app.schema.postgres_enums import CampaignStatusEnum
from app.utils.pgdb import pool


async def create_campaign(project_name, version):
    """Insert into campaign a new empty occurrence"""
    _version, __ = await get_version_and_collection(project_name, version)
    if _version is None:
        raise VersionNotFound(f"{version} does not belong to {project_name}.")
    with pool.connection() as connection:
        connection.row_factory = dict_row
        conn = connection.execute("insert into campaigns (project_id, version, status) "
                                  "values (%s, %s, %s)"
                                  "returning project_id as project_name, "
                                  "version as version, occurrence as occurrence, "
                                  "description as description, status as status;",
                                  (project_name.casefold(), _version,
                                   CampaignStatusEnum.recorded)).fetchone()

        connection.commit()
        return conn


async def retrieve_campaign(project_name,
                      version: str = None,
                      status: str = None,
                      limit: int = 10,
                      skip: int = 0):
    """Get raw campaign with version, occurrence, description and status"""
    with pool.connection() as connection:
        connection.row_factory = dict_row
        if version is None and status is None:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, limit, skip))
        elif version is None:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s"
                                      " and status = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, status, limit, skip))
        elif status is None:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      " and version = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, version, limit, skip))
        else:
            conn = connection.execute("select id as id, project_id as project_id,"
                                      " version as version, occurrence as occurrence,"
                                      " description as description, "
                                      " status as status "
                                      "from campaigns "
                                      "where project_id = %s "
                                      " and version = %s"
                                      " and status = %s "
                                      "order by version desc, occurrence desc "
                                      "limit %s offset %s;",
                                      (project_name, version, status, limit, skip))
        count = connection.execute("select count(*) as total "
                                   "from campaigns "
                                   "where project_id = %s;", (project_name,))
        return conn.fetchall(), count.fetchone()["total"]


async def retrieve_campaign_id(project_name: str, version: str, occurrence: str):
    """get campaign internal id and status"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute("select id, status"
                                  " from campaigns"
                                  " where project_id = %s "
                                  " and version = %s "
                                  " and occurrence = %s;",
                                  (project_name, version, occurrence)).fetchone()


async def retrieve_all_campaign_id_for_version(project_name: str, version: str):
    """Get campaigns internal id and status"""
    with pool.connection() as connection:
        connection.row_factory = tuple_row
        return connection.execute("select id, status"
                                  " from campaigns"
                                  " where project_id = %s "
                                  " and version = %s ",
                                  (project_name, version)).fetchall()


async def is_campaign_exist(project_name: str, version: str, occurrence: str):
    """Check if campaign exist"""
    return bool(await retrieve_campaign_id(project_name, version, occurrence))
