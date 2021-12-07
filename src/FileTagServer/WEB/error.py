from pystache.renderer import Renderer
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse


def add_routes(app: FastAPI, renderer: Renderer):
    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException):
        allowed = [301, 303, 307, 400, 404, 410, 418]

        if exc.status_code not in allowed:
            raise exc

        query = f"../static/html/error/{exc.status_code}.html"
        html = renderer.render_path(query)
        return HTMLResponse(content=html, status_code=exc.status_code)
