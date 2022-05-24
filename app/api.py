# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import (projects,
                         settings,
                         front_dashboard,
                         version)
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(front_dashboard.router)
app.include_router(version.router)
