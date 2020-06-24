from os.path import splitext, dirname, join
from typing import Dict, Optional, Tuple, Union, Callable
import src.PathUtil as PathUtil
from litespeed import serve, route


# Lists entry points for grabbing files; due to how serve functions, we cannot go up levels, which means we can restrict what we expose to the client
# To do this, we expose specific routes, which only expose the smallest folder amount of content possible

# initializes global module variables if need be
# also ensures that the module isn't considered unnecessary by python
def init() -> None:
    pass


# Convert a virtual path from the browser to a real path on the file system
def virtual_to_real_path(file: str, virtual_path: Union[Callable[[str], str], str] = None) -> str:
    real_path = file
    if virtual_path is not None:
        if hasattr(virtual_path, '__call__'):
            real_path = virtual_path(real_path)
        else:
            real_path = join(virtual_path, real_path)
    return real_path


@route("css/(.*)", no_end_slash=True)
def css(request, file: str):
    vpath = PathUtil.css_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


@route("js/(.*)", no_end_slash=True)
def javascript(request, file):
    vpath = PathUtil.js_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)


@route("images/(.*)")
def images(request, file):
    vpath = PathUtil.image_path
    rpath = virtual_to_real_path(file, vpath)
    return serve(rpath)
