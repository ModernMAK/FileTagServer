from typing import Dict

from fastapi import FastAPI
from fastapi.datastructures import Default
from pystache import Renderer
from starlette.responses import HTMLResponse

from FileTagServer.DBI.webconverter import WebConverter
from FileTagServer.WEB.app import LocalPathConfig
from FileTagServer.WEB.index import get_folder_icon, get_file_icon
from FileTagServer.WEB.routing import folder_route, tag_route, file_route, file_data_route, file_preview_route


def create_fastapi_kwargs(**kwargs) -> Dict:
    # Default to none for any api/doc urls
    default_none_keys = ["openapi_url", "docs_url", "redoc_url"]
    for key in default_none_keys:
        kwargs[key] = None if key not in kwargs else kwargs[key]

    # Default to HTML Response (unless overriden)
    kwargs["default_response_class"] = Default(HTMLResponse) if "default_response_class" not in kwargs else kwargs[
        "default_response_class"]
    return kwargs


def create_renderer(local_pathing: LocalPathConfig = None, **kwargs):
    if "search_dirs" not in kwargs and local_pathing:
        kwargs["search_dirs"] = str(local_pathing.templates)
    return Renderer(**kwargs)


def create_webconv() -> WebConverter:
    return WebConverter(
        folder_route,
        get_folder_icon,
        file_route,
        file_preview_route,
        get_file_icon,
        tag_route
    )
