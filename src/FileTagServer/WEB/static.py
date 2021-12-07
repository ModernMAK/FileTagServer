from os.path import join
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def mount(app: FastAPI, static_root: str = None):
    static_root = static_root or "../static"
    app.mount("/js", StaticFiles(directory=join(static_root, "js")), name="JavaScript")
    app.mount("/css", StaticFiles(directory=join(static_root, "css")), name="Cascading Style Sheet")
    # app.mount("/img", StaticFiles(directory=join(static_root, "img")), name="Images")
