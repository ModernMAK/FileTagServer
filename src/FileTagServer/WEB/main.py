from http import HTTPStatus

from fastapi import FastAPI
from starlette.responses import RedirectResponse

from FileTagServer.WEB.app import add_routes
from FileTagServer.WEB.routing import files_route
from FileTagServer.WEB.common import web_app
from FileTagServer.WEB.error import dummy as dummy_error
# from FileTagServer.WEB.file import dummy as dummy_file
from FileTagServer.WEB.static import dummy as dummy_static
# from FileTagServer.WEB.forms import dummy as dummy_form
# from FileTagServer.WEB.folder import dummy as dummy_folder
import uvicorn


def init():
    dummy_error()
    # dummy_file()
    # dummy_folder()
    dummy_static()
    # dummy_form()

    # @web_app.get("/")
    # def index():
    #     return RedirectResponse(files_route, HTTPStatus.SEE_OTHER)


def run(**kwargs):
    init()
    add_routes(web_app)
    uvicorn.run(web_app, **kwargs)


if __name__ == "__main__":
    run(host="localhost", port=80)
