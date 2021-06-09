from FileTagServer.WEB.common import web_app
from fastapi.staticfiles import StaticFiles


def dummy():
    pass


web_app.mount("/js", StaticFiles(directory="../static/js"), name="JavaScript")
web_app.mount("/css", StaticFiles(directory="../static/css"), name="Cascading Style Sheet")
