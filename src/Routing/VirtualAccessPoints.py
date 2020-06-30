from os.path import join
from typing import Union, Callable

from litespeed import serve, route
from src.DbUtil import Conwrapper
import src.PathUtil as PathUtil
from src.API.ModelClients import File as FileClient


# Lists entry points for grabbing files; due to how route functions, we cannot go up levels,
# which means we can restrict what we expose to the client
# To do this, we expose specific routes, which only expose the smallest folder amount of content possible


# Previously import would load all routes imported
# This way we can control routes being added
def add_routes() -> None:
    route("css/(.*)", f=css, no_end_slash=True, methods=['GET'])
    route("js/(.*)", f=javascript, no_end_slash=True, methods=['GET'])
    route("images/(.*)", f=images, no_end_slash=True, methods=['GET'])
    route("media/(.*)", f=media, no_end_slash=True, methods=['GET'])
    route("file/(\d+)", f=file, no_end_slash=True, methods=['GET'])


# Convert a virtual path from the browser to a real path on the file system
def virtual_to_real_path(file: str, virtual_path: Union[Callable[[str], str], str] = None) -> str:
    real_path = file
    if virtual_path is not None:
        if hasattr(virtual_path, '__call__'):
            real_path = virtual_path(real_path)
        else:
            real_path = join(virtual_path, real_path)
    return real_path


def css(request, file: str):
    vpath = PathUtil.css_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def javascript(request, file: str):
    vpath = PathUtil.js_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def images(request, file: str):
    vpath = PathUtil.image_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def media(request, file: str):
    vpath = PathUtil.media_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def file(request, file: int):
    f_client = FileClient(db_path=PathUtil.data_path('mediaserver.db'))
    results = f_client.get(ids=[file])
    if results is None or len(results) < 1:
        return None, 404
    rpath = results[0]['real_path']
    return serve(rpath)

# html does not have a virtual path as we do not want to expose the raw html / pystache
# We dont want to expose web for similair reasons
