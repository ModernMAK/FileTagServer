from FileTagServer.WEB.common import web_app
from FileTagServer.WEB.error import dummy as dummy_error
from FileTagServer.WEB.file import dummy as dummy_file
from FileTagServer.WEB.static import dummy as dummy_static
import uvicorn

dummy_error()
dummy_file()
dummy_static()


def run(**kwargs):
    uvicorn.run(web_app, **kwargs)


if __name__ == "__main__":
    run(host="localhost", port=80)
