import os.path as path
from typing import Union


# These should not be used to output to the html files
# Routes should be used to point to Access Points

def project_root() -> str:
    return path.dirname(path.dirname(__file__))


def join_helper(root_dir: str, html_dir: str, requested_path: Union[str, None]) -> str:
    if requested_path:
        return path.join(root_dir, html_dir, requested_path)
    else:
        return path.join(root_dir, html_dir)


def web_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web"
    return join_helper(root_dir, html_dir, requested_path)


def html_path(requested_path: str = None) -> str:
    root_dir = web_path()
    html_dir = "html"
    return join_helper(root_dir, html_dir, requested_path)


def css_path(requested_path: str = None) -> str:
    root_dir = web_path()
    html_dir = "css"
    return join_helper(root_dir, html_dir, requested_path)


def js_path(requested_path: str = None) -> str:
    root_dir = web_path()
    html_dir = "js"
    return join_helper(root_dir, html_dir, requested_path)


def media_path(requested_path: str = None) -> str:
    root_dir = web_path()
    html_dir = "media"
    return join_helper(root_dir, html_dir, requested_path)


def image_path(requested_path: str = None) -> str:
    root_dir = media_path()
    html_dir = "images"
    return join_helper(root_dir, html_dir, requested_path)


def data_path(requested_path: str = None) -> str:
    root_dir = web_path()
    html_dir = "data"
    return join_helper(root_dir, html_dir, requested_path)


def html_image_path(requested_path: str = None) -> str:
    root_dir = html_path()
    html_dir = 'image'
    return join_helper(root_dir, html_dir, requested_path)


def html_tag_path(requested_path: str = None) -> str:
    root_dir = html_path()
    html_dir = "tag"
    return join_helper(root_dir, html_dir, requested_path)
