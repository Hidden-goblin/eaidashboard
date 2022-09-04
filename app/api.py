# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.database.authentication import init_user_token
from app.database.users import init_user
from app.database.postgres import init_postgres, update_postgres
from app.routers import (projects,
                         settings,
                         front_dashboard,
                         version,
                         users,
                         auth,
                         bugs)
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
              })

init_postgres()
update_postgres()

app.add_middleware(SessionMiddleware, secret_key='toto')

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(front_dashboard.router)
app.include_router(version.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bugs.router)

init_user()
init_user_token()

@app.on_event("startup")
def db_start_connection():
    pool.open()


@app.on_event("shutdown")
def db_start_connection():
    pool.close()
