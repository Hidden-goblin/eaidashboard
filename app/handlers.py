from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.app_exception import ProjectNotRegistered


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectNotRegistered)
    async def project_not_registered_handler(request: Request, exc: ProjectNotRegistered) -> Response:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.detail},
        )

    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc: HTTPException) -> Response:
        path = request.url.path

        if path.startswith("/api"):
            return JSONResponse(
                status_code=404,
                content={"detail": exc.detail or "Not Found"},
            )
        else:
            return RedirectResponse("/")
