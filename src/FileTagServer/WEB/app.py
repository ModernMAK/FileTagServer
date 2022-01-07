from pathlib import PurePath, PurePosixPath as PureWebPath
from typing import Any, Optional

from fastapi import FastAPI
from pystache import Renderer

from FileTagServer.DBI.database import Database
from FileTagServer.DBI.webconverter import WebConverter
from FileTagServer.WEB.content import PreviewManager


class LocalPathConfig:
    def __init__(self, root: Optional[str], static: str = None, generated: str = None):
        self.root = PurePath(root or "web")  # cwd/web
        self.static = self.root / (static or "static")  # cwd/web/static
        self.html = self.static / "html"
        self.css = self.static / "css"
        self.js = self.static / "js"
        self.img = self.static / "img"
        self.html_templates = self.html / "templates"
        self.js_templates = self.js / "templates"
        self.sql = self.static / "sql"
        self.generated = self.root / (generated or "generated")
        self.previews = self.generated / "previews"


class RemotePathConfig:
    def __init__(self, root: str = None, static: str = None):
        self.root = PureWebPath(root or "/")  # cwd/web
        self.static = (self.root / static if static else self.root)  # cwd/web/static
        self.html = self.static / "html"
        self.css = self.static / "css"
        self.js = self.static / "js"
        self.img = self.static / "img"


class WebsiteApp(FastAPI):
    def __init__(self, renderer: Renderer, database: Database, webconv: WebConverter, local_pathing: LocalPathConfig, remote_pathing: RemotePathConfig, previews:PreviewManager, **fastapi_kwargs: Any):
        super().__init__(**fastapi_kwargs)
        self.renderer = renderer
        self.database = database
        self.webconv = webconv
        self.local_pathing = local_pathing
        self.remote_pathing = remote_pathing
        self.previews = previews