from fastapi import FastAPI
from pystache import Renderer

from FileTagServer.DBI.database import Database
from FileTagServer.DBI.webconverter import WebConverter
from FileTagServer.WEB.common import create_renderer, create_app_instance
from FileTagServer.WEB import error, static, app as application
from FileTagServer.WEB.app import create_webconv
import uvicorn


def init(app: FastAPI, renderer: Renderer, database: Database, conv: WebConverter):
    error.add_routes(app, renderer)
    static.mount(app)
    application.add_routes(app, renderer, database, conv)

    # @web_app.get("/")
    # def index():
    #     return RedirectResponse(files_route, HTTPStatus.SEE_OTHER)


def run(db_path: str, **kwargs):
    db = Database(db_path)
    app = create_app_instance()
    renderer = create_renderer()
    conv = create_webconv()
    init(app, renderer, db, conv)
    uvicorn.run(app, **kwargs)


if __name__ == "__main__":
    db_path = r"C:\Users\andre\Documents\GitHub\FileTagServer\local.db"
    run(db_path=db_path, host="localhost", port=80)
