# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database.postgre.postgres import init_postgres, update_postgres
from app import conf
from app.conf import config
from app.database.utils.password_management import generate_keys
from app.utils.pgdb import pool

def check_transition():
    with pool.connection() as conn:
        res = conn.execute("select op_order, content "
                           "from operations "
                           "where type='migration_redis' order by op_order DESC;")
        row = res.fetchone()
        print(row)
        if row is not None and row[0] == 7:
            conf.MIGRATION_DONE = True

check_transition()
if conf.MIGRATION_DONE:
    from app.database.postgre.pg_users import init_user
    from app.database.postgre.postgres import postgre_register
else:
    from app.database.mongo.tokens import init_user_token
    from app.database.mongo.mongo import mongo_register, update_mongodb
    from app.database.mongo.users import init_user

from app.routers.rest import (auth, bugs, project_campaigns, project_repository, projects,
                              settings, users, version, project_test_results, migration)
from app.routers.front import (front_dashboard, front_projects, front_projects_campaign,
                               front_projects_bug, front_projects_repository, front_forms)
from app.utils.openapi_tags import DESCRIPTION


description = """\
Eaidashboard is a simple api and front to monitor test activities.
"""
app = FastAPI(title="Eaidashboard",
              description=description,
              version="2.9",
              license_info={
                  "name": "GNU GPL v3",
                  "url": "https://www.gnu.org/licenses/gpl-3.0.en.html"
              },
              openapi_tags=DESCRIPTION,
              docs_url=None)

init_postgres()
update_postgres()
if not conf.MIGRATION_DONE:
    update_mongodb()

app.add_middleware(SessionMiddleware, secret_key=config["SESSION_KEY"])
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(front_dashboard.router)
app.include_router(version.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bugs.router)
app.include_router(project_test_results.router)
app.include_router(project_repository.router)
app.include_router(project_campaigns.router)
app.include_router(front_projects.router)
app.include_router(front_projects_campaign.router)
app.include_router(front_projects_bug.router)
app.include_router(front_projects_repository.router)
app.include_router(front_forms.router)
app.include_router(migration.router)

init_user()
if not conf.MIGRATION_DONE:
    init_user_token()
else:
    generate_keys()


@app.on_event("startup")
def db_start_connection():
    pool.open()
    if not conf.MIGRATION_DONE:
        mongo_register()
    else:
        postgre_register()


@app.on_event("shutdown")
def db_start_connection():
    pool.close()


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url=app.openapi_url,
                               title=f"{app.title} - Swagger UI",
                               oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                               swagger_js_url="/assets/swagger-ui-bundle.js",
                               swagger_css_url="/assets/swagger-ui.css")


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

