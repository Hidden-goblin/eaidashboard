# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from markdown import markdown
from markdown.extensions.toc import TocExtension
from starlette.requests import Request

from app.conf import APP_VERSION, BASE_DIR, templates

router = APIRouter(prefix="/documentation")


@router.get("/",
            include_in_schema=False)
async def root_document(request: Request,
                        page: str = "index.md"):
    return templates.TemplateResponse("documentation.html",
                                      {"request": request,
                                       "first": page,
                                       "app_version": APP_VERSION})


@router.get("/{filename}",
            include_in_schema=False)
async def serve_document(filename: str,
                         request: Request):
    with open(Path(BASE_DIR) / "documentation" / filename, "r") as f:
        return HTMLResponse(content=markdown(f.read(), extensions=['fenced_code',
                                                                   TocExtension(baselevel=2,
                                                                                title='Contents')]),
                            headers={"HX-Retarget": "#docContainer"})
