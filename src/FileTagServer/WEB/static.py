from os.path import join
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from FileTagServer.WEB.app import WebsiteApp


def mount(app: WebsiteApp):
    app.mount(str(app.remote_pathing.js), StaticFiles(directory=app.local_pathing.js), name="JavaScript")
    app.mount(str(app.remote_pathing.css), StaticFiles(directory=app.local_pathing.css), name="Cascading Style Sheet")
    app.mount(str(app.remote_pathing.img), StaticFiles(directory=app.local_pathing.img), name="Images")
