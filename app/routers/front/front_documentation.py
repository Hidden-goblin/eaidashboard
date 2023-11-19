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
                        page: str = "index.md") -> HTMLResponse:
    return templates.TemplateResponse("documentation.html",
                                      {"request": request,
                                       "first": page,
                                       "app_version": APP_VERSION},
                                      headers={"HX-Retarget": "#content-block"})


@router.get("/{filename}",
            include_in_schema=False)
async def serve_document(filename: str,
                         request: Request) -> HTMLResponse:
    with open(Path(BASE_DIR) / "documentation" / filename) as f:
        return HTMLResponse(content=css_wrapper(markdown(f.read(),
                                                         extensions=['fenced_code',
                                                                     'tables',
                                                                     'attr_list',
                                                                     TocExtension(baselevel=2,
                                                                                  title='Contents')])),
                            headers={"HX-Retarget": "#docContainer"})


def css_wrapper(content: str) -> str:
    return content.replace("<table>", '<table class="table table-striped table-hover">')
