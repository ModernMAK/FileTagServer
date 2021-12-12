from pystache.renderer import Renderer
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse

from FileTagServer.WEB.app import WebsiteApp


def add_routes(app: WebsiteApp):
    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException):
        allowed = [301, 303, 307, 400, 404, 410, 418]

        if exc.status_code not in allowed:
            raise exc

        query = app.local_pathing.html / f"error/{exc.status_code}.html"
        html = app.renderer.render_path(query)
        return HTMLResponse(content=html, status_code=exc.status_code)
