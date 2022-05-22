# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import projects, settings, front_dashboard

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(front_dashboard.router)
