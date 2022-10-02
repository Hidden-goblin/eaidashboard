# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database.authentication import init_user_token
from app.database.users import init_user
from app.database.postgres import init_postgres, update_postgres
from app.routers.rest import auth, bugs, project_campaigns, project_repository, projects, \
    settings, \
    users, version
from app.routers.front import front_dashboard, front_projects
from app.utils.openapi_tags import DESCRIPTION
from app.utils.pgdb import pool

description = """\
Eaidashboard is a simple api and front to monitor test activities.
"""
app = FastAPI(title="Eaidashboard",
              description=description,
              version="1.1",
              license_info={
                  "name": "GNU GPL v3",
                  "url": "https://www.gnu.org/licenses/gpl-3.0.en.html"
              },
              openapi_tags=DESCRIPTION)

init_postgres()
update_postgres()

app.add_middleware(SessionMiddleware, secret_key='toto')
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
app.include_router(project_repository.router)
app.include_router(project_campaigns.router)
app.include_router(front_projects.router)

init_user()
init_user_token()


@app.on_event("startup")
def db_start_connection():
    pool.open()


@app.on_event("shutdown")
def db_start_connection():
    pool.close()
