# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.conf import APP_VERSION, config
from app.database.postgre.pg_users import init_user
from app.database.postgre.postgres import init_postgres, postgre_register, update_postgres
from app.database.utils.password_management import generate_keys
from app.routers.front import (
    front_dashboard,
    front_documentation,
    front_forms,
    front_projects,
    front_projects_bug,
    front_projects_campaign,
    front_projects_repository,
)
from app.routers.rest import (
    auth,
    bugs,
    project_campaigns,
    project_repository,
    project_test_results,
    projects,
    settings,
    users,
    version,
)
from app.utils.log_management import log_message
from app.utils.openapi_tags import DESCRIPTION
from app.utils.pgdb import pool

init_postgres()
update_postgres()

description = """\
Eaidashboard is a simple api and front to monitor test activities.
"""
app = FastAPI(title="Eaidashboard",
              description=description,
              version=APP_VERSION,
              license_info={
                  "name": "GNU GPL v3",
                  "url": "https://www.gnu.org/licenses/gpl-3.0.en.html"
              },
              openapi_tags=DESCRIPTION,
              docs_url=None)


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
app.include_router(front_documentation.router)

log_message(f"Postgre: {config.get('PG_URL')}:{config.get('PG_PORT')}, {config.get('PG_DB')}\n"
            f"Redis: {config.get('REDIS_URL')}:{config.get('REDIS_PORT')}")

init_user()

generate_keys()


@app.on_event("startup")
def db_start_connection() -> None:
    pool.open()
    postgre_register()


@app.on_event("shutdown")
def db_close_connection():
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
