import uvicorn

from FileTagServer.DBI.database import Database
from FileTagServer.WEB import error, static, index
from FileTagServer.WEB.app import WebsiteApp, LocalPathConfig, RemotePathConfig
from FileTagServer.WEB.common import create_renderer, create_fastapi_kwargs, create_webconv
from FileTagServer.WEB.content import PreviewManager


def init(app: WebsiteApp):
    error.add_routes(app)
    static.mount(app)
    index.add_routes(app)


def init_default(db_path: str, local_pathing: LocalPathConfig=None, remote_pathing: RemotePathConfig = None) -> WebsiteApp:
    local_pathing = local_pathing or LocalPathConfig(None)
    remote_pathing = remote_pathing or RemotePathConfig()  # default SHOULD be valid
    db = Database(db_path, local_pathing.sql)
    fastapi_kwargs = create_fastapi_kwargs()
    renderer = create_renderer(local_pathing)
    conv = create_webconv()
    previews = PreviewManager(local_pathing.previews)
    app = WebsiteApp(renderer, db, conv, local_pathing, remote_pathing, previews, **fastapi_kwargs)
    init(app)
    return app


def run(db_path: str, local_pathing: LocalPathConfig, remote_pathing: RemotePathConfig = None, **kwargs):
    app = init_default(db_path, local_pathing, remote_pathing)
    uvicorn.run(app, **kwargs)
