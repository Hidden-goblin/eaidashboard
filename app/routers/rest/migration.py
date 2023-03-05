# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import datetime
from typing import Any

from pymongo import MongoClient
from fastapi import APIRouter, HTTPException, Security

from app import conf
from app.database.authorization import authorize_user

from app.conf import mongo_string
from app.database.mongo.bugs import get_bugs
from app.database.mongo.db_settings import DashCollection
from app.database.mongo.projects import get_projects
from app.database.mongo.versions import get_version, get_versions
from app.database.postgre.pg_projects import register_project
from app.utils.pgdb import pool
from app.utils.project_alias import provide
from app.utils.redis import redis_health

router = APIRouter(
    prefix="/api/v1/admin"
)

@router.get("/redis_migration",
            tags=["Admin"])
async def migrate_redis(user: Any = Security(authorize_user, scopes=["admin"])):
    try:
        # Check transition
        if conf.MIGRATION_DONE:
            raise Exception("Migration done nothing to do")
        # Check Redis alive
        if not redis_health():
            raise Exception("Redis not ready")

        client = MongoClient(mongo_string)
        # Users
        db = client["settings"]
        collection = db["users"]
        users = collection.find({})
        users_result = {"mongo": [],
                        "postgres": []}
        with pool.connection() as conn:
            for user in users:
                res = conn.execute("insert into users (username, password, scopes) "
                             "values (%s, %s, %s) "
                             "on conflict do nothing;",
                             (user["username"], user["password"], user["scopes"]))
                users_result["mongo"].append(user["username"])
                users_result["postgres"].append((user["username"], res.statusmessage))
                conn.commit()

            conn.execute("insert into operations (type, op_user, op_order, content) "
                         "values ('migration_redis', 'application', 1, 'User migration done')"
                         " on conflict do nothing;")
            conn.commit()

            projects = await get_projects(0, 1000)
            projects_result = {"mongo": [],
                               "postgres": []}
            for project in projects:
                res = conn.execute("insert into projects (name, alias) "
                             "values (%s, %s) "
                             "on conflict do nothing;",
                             (project["name"].casefold(), provide(project["name"])))
                projects_result["mongo"].append(project["name"])
                projects_result["postgres"].append((project["name"], res.statusmessage))
                conn.commit()
            conn.execute("insert into operations (type, op_user, op_order, content) "
                             "values ('migration_redis', 'application', 2, 'Project migration done')"
                             " on conflict do nothing;")
            conn.commit()
            versions_result = []
            for project in projects:
                # Migrate versions
                versions_result.append(await migrate_versions(project["name"]))
            conn.execute("insert into operations (type, op_user, op_order, content) "
                         "values ('migration_redis', 'application', 3, 'Project versions migration done')"
                         " on conflict do nothing;")
            conn.commit()

            tickets_result = []
            for project in projects:
                # Migrate tickets
                tickets_result.append(await migrate_tickets(project["name"]))

            conn.execute("insert into operations (type, op_user, op_order, content) "
                         "values ('migration_redis', 'application', 4, 'Project tickets migration "
                         "done')"
                         " on conflict do nothing;")
            conn.commit()
            conn.execute("update campaign_tickets as ct "
                         "set ticket_id = sub.ticket_id "
                         "from (select tk.id as ticket_id, tk.reference as reference, cp.id as campaign_id"
                         "      from tickets as tk "
                         "      join projects as pjt on tk.project_id = pjt.id "
                         "      join versions as ve on tk.current_version = ve.id "
                         "      join campaigns as cp on pjt.name = cp.project_id "
                         "      where cp.version = ve.version) as sub "
                         "where ct.campaign_id = sub.campaign_id "
                         "and ct.ticket_reference = sub.reference;")
            conn.commit()
            conn.execute("insert into operations (type, op_user, op_order, content) "
                         "values ('migration_redis', 'application', 5, 'Bind campaign_tickets with tickets')"
                         " on conflict do nothing;")
            conn.commit()
            bugs_result = []
            for project in projects:
                # Migrate bugs
                bugs_result.append(await migrate_bugs(project["name"]))
            conn.execute("insert into operations (type, op_user, op_order, content) "
                         "values ('migration_redis', 'application', 6, 'Project bugs migration')"
                         " on conflict do nothing;")
            conn.commit()

            conn.execute("insert into operations (type, op_user, op_order, content) "
                         "values ('migration_redis', 'application', 7, 'Migration completed')"
                         " on conflict do nothing;")
            conn.commit()
            conf.MIGRATION_DONE = True
        return {"users": users_result,
                "projects": projects_result,
                "versions": versions_result,
                "tickets": tickets_result,
                "bugs": bugs_result}
    except Exception as exp:
        return HTTPException(500, ', '.join(exp.args))

async def migrate_versions(project_name):
    versions = await get_versions(project_name)
    versions_result = {"mongo": [],
                       "postgres": []}
    with pool.connection() as conn:
        for version in versions:
            _version = await get_version(project_name, version)
            res = conn.execute("insert into versions (project_id, version, created, updated, started, end_forecast, status, open, cancelled, blocked, in_progress, done, open_blocking, open_major, open_minor, closed_blocking, closed_major, closed_minor)"
                         "select id, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s from projects where alias = %s "
                         "on conflict do nothing;",
                         (version,
                          _version.get("created", datetime.datetime.now()),
                          _version.get("updated", datetime.datetime.now()),
                          _version.get("started", None),
                          _version.get("end_forecast", None),
                          _version.get("status"),
                          _version.get("statistics", {}).get("open", 0),
                          _version.get("statistics", {}).get("cancelled", 0),
                          _version.get("statistics", {}).get("blocked", 0),
                          _version.get("statistics", {}).get("in_progress", 0),
                          _version.get("statistics", {}).get("done", 0),
                          _version.get("bugs", {}).get("open_blocking", 0),
                          _version.get("bugs", {}).get("open_major", 0),
                          _version.get("bugs", {}).get("open_minor", 0),
                          _version.get("bugs", {}).get("closed_blocking", 0),
                          _version.get("bugs", {}).get("closed_major", 0),
                          _version.get("bugs", {}).get("closed_minor", 0),
                          provide(project_name)))
            versions_result["mongo"].append((project_name, version))
            versions_result["postgres"].append((project_name, version, res.statusmessage))
            conn.commit()
    return versions_result

async def migrate_tickets(project_name):
    client = MongoClient(mongo_string)
    db = client[provide(project_name)]
    tickets = db[DashCollection.TICKETS.value].find({})
    tickets_result = {"mongo": [],
                      "postgres": []}
    with pool.connection() as conn:
        for ticket in tickets:
            res = conn.execute("insert into tickets (reference, description, status, created, updated, current_version, project_id) "
                         "select %s, %s, %s, %s, %s, ve.id, pjt.id "
                         "from projects as pjt "
                         "join versions as ve on pjt.id = ve.project_id "
                         "where pjt.alias = %s and ve.version = %s "
                         " on conflict do nothing;",
                         (ticket.get("reference"),
                          ticket.get("description", ""),
                          ticket.get("status"),
                          ticket.get("created", datetime.datetime.now()),
                          ticket.get("updated", datetime.datetime.now()),
                          provide(project_name),
                          ticket.get("version")))
            tickets_result["mongo"].append((project_name, ticket.get("version"), ticket.get("reference")))
            tickets_result["postgres"].append(
                (project_name, ticket.get("version"), ticket.get("reference"), res.statusmessage))
            conn.commit()
    return tickets_result


async def migrate_bugs(project_name):
    bugs = await get_bugs(project_name)
    bugs_result = {"mongo": [],
                   "postgres": []}
    with pool.connection() as conn:
        for bug in bugs:
            res = conn.execute("insert into bugs (title, url, description, status, created, updated, criticality, project_id, version_id)"
                         "select %s, %s, %s, %s, %s, %s, %s, ve.project_id, ve.id from versions as ve "
                         "join projects as pjt on pjt.id = ve.project_id "
                         "where pjt.alias = %s and ve.version = %s "
                         "on conflict do nothing;",
                         (bug.get("title"),
                          bug.get("url"),
                          bug.get("description"),
                          bug.get("status"),
                          bug.get("created", datetime.datetime.now()),
                          bug.get("updated", datetime.datetime.now()),
                          bug.get("criticality"),
                          provide(project_name),
                          bug.get("version")))
            bugs_result["mongo"].append((project_name, bug.get("version"), bug.get("title")))
            bugs_result["postgres"].append((project_name, bug.get("version"), bug.get("title"), res.statusmessage))
            # update_query = (f"update versions as ve"
            #                 f" set {bug.get('status')}_{bug.get('criticality')}"
            #                 f" = {bug.get('status')}_{bug.get('criticality')} + 1"
            #                 f" from projects as pj"
            #                 f" where pj.alias = %s"
            #                 f" and pj.id = ve.project_id"
            #                 f" and ve.version = %s;")
            # conn.execute(update_query, (provide(project_name), bug.get("version")))
            conn.commit()
    return bugs_result