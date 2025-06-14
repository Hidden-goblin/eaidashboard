# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse

from app.conf import APP_VERSION, config
from app.database.postgre.pg_users import init_user
from app.database.postgre.postgres import init_postgres, postgre_register, update_postgres
from app.database.utils.password_management import generate_keys
from app.routers import monitoring
from app.routers.front import (
    front_dashboard,
    front_documentation,
    front_project_version_tickets,
    front_projects,
    front_projects_bug,
    front_projects_campaign,
    front_projects_repository,
    front_users,
    front_versions,
)
from app.routers.rest import (
    async_status,
    auth,
    bugs,
    project_campaigns,
    project_repository,
    project_test_results,
    projects,
    settings,
    tickets,
    users,
    version,
)
from app.routers.rest.repository import (
    rest_epics,
    rest_features,
    rest_scenarios,
)
from app.utils.log_management import log_message
from app.utils.openapi_tags import DESCRIPTION
from app.utils.pgdb import pool

logger = getLogger(__name__)

init_postgres()
update_postgres()

description = """\
Eaidashboard is a simple api and front to monitor test activities.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    logger.info("Startup process")
    pool.open()
    postgre_register()
    yield
    pool.close()


app = FastAPI(
    title="Eaidashboard",
    description=description,
    version=APP_VERSION,
    license_info={"name": "GNU GPL v3", "url": "https://www.gnu.org/licenses/gpl-3.0.en.html"},
    openapi_tags=DESCRIPTION,
    docs_url=None,
    swagger_ui_parameters={"swagger": "2.0"},
    lifespan=lifespan,
)


app.add_middleware(
    SessionMiddleware,
    secret_key=config["SESSION_KEY"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

app.include_router(monitoring.router)
app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(front_dashboard.router)
app.include_router(version.router)
app.include_router(tickets.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bugs.router)
app.include_router(project_test_results.router)
app.include_router(project_repository.router)
app.include_router(project_campaigns.router)
app.include_router(rest_epics.router)
app.include_router(rest_scenarios.router)
app.include_router(rest_features.router)
app.include_router(async_status.router)
app.include_router(front_projects.router)
app.include_router(front_projects_campaign.router)
app.include_router(front_projects_bug.router)
app.include_router(front_projects_repository.router)
app.include_router(front_documentation.router)
app.include_router(front_users.router)
app.include_router(front_project_version_tickets.router)
app.include_router(front_versions.router)

Instrumentator(
    # should_respect_env_var=True,
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app)

log_message(
    f"\nPostgresql on: {config.get('PG_URL')}:{config.get('PG_PORT')}, {config.get('PG_DB')}\n"
    f"Redis on: {config.get('REDIS_URL')}:{config.get('REDIS_PORT')}"
)

init_user()

generate_keys()


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/assets/5_swagger-ui-bundle.js",
        swagger_css_url="/assets/5_swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    return get_swagger_ui_oauth2_redirect_html()
