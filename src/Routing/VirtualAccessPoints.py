from os.path import join
from typing import Union, Callable

from litespeed import serve, route
import src.PathUtil as PathUtil


# Lists entry points for grabbing files; due to how route functions, we cannot go up levels,
# which means we can restrict what we expose to the client
# To do this, we expose specific routes, which only expose the smallest folder amount of content possible

def initialize_module(**kwargs):
    pass


def add_routes() -> None:
    route(r"css/(.*)", f=css, no_end_slash=True, methods=['GET'])
    route(r"js/(.*)", f=javascript, no_end_slash=True, methods=['GET'])
    route(r"images/(.*)", f=images, no_end_slash=True, methods=['GET'])
    route(r"media/(.*)", f=media, no_end_slash=True, methods=['GET'])
    route(r"dyn/gen/(.*)", f=dynamic_generated, no_end_slash=True, methods=['GET'])


# Convert a virtual path from the browser to a real path on the file system
def virtual_to_real_path(file: str, virtual_path: Union[Callable[[str], str], str] = None) -> str:
    real_path = file
    if virtual_path is not None:
        if hasattr(virtual_path, '__call__'):
            real_path = virtual_path(real_path)
        else:
            real_path = join(virtual_path, real_path)
    return real_path


# Convert a real path on the file system to a virtual path from the browser
# This assumes that the 'real_path' portion of the file is known beforehand
def real_to_virtual_path(file: str, real_path: Union[Callable[[str], str], str] = None) -> str:
    virtual_path = file
    if real_path is not None:
        if hasattr(real_path, '__call__'):
            virtual_path = virtual_path.replace(real_path(), '')
        else:
            virtual_path = virtual_path.replace(real_path, '')
    return virtual_path


def css(request, file: str):
    vpath = PathUtil.css_real_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def javascript(request, file: str):
    vpath = PathUtil.js_real_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def images(request, file: str):
    vpath = PathUtil.image_real_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


def media(request, file: str):
    vpath = PathUtil.media_real_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)

def dynamic_generated(request, file: str):
    vpath = PathUtil.dynamic_generated_real_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)

# html does not have a virtual path as we do not want to expose the raw html / pystache
# We dont want to expose web for the same reason
