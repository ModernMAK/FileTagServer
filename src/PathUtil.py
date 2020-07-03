import os.path as path
from typing import Union


# These should not be used to output to the html files
# Routes should be used to point to Access Points

def project_root() -> str:
    return path.dirname(path.dirname(__file__))


def root_path(requested_path: Union[str, None]) -> str:
    if requested_path:
        return path.join(project_root(), requested_path)
    else:
        return project_root()


def join_helper(root_dir: str, html_dir: str, requested_path: Union[str, None]) -> str:
    if requested_path:
        return path.join(root_dir, html_dir, requested_path)
    else:
        return path.join(root_dir, html_dir)


def web_real_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web"
    return join_helper(root_dir, html_dir, requested_path)


def html_real_path(requested_path: str = None) -> str:
    root_dir = web_real_path()
    html_dir = "html"
    return join_helper(root_dir, html_dir, requested_path)


def css_real_path(requested_path: str = None) -> str:
    root_dir = web_real_path()
    html_dir = "css"
    return join_helper(root_dir, html_dir, requested_path)


def js_real_path(requested_path: str = None) -> str:
    root_dir = web_real_path()
    html_dir = "js"
    return join_helper(root_dir, html_dir, requested_path)


def media_real_path(requested_path: str = None) -> str:
    root_dir = web_real_path()
    html_dir = "media"
    return join_helper(root_dir, html_dir, requested_path)


def image_real_path(requested_path: str = None) -> str:
    root_dir = media_real_path()
    html_dir = "images"
    return join_helper(root_dir, html_dir, requested_path)


def data_real_path(requested_path: str = None) -> str:
    root_dir = web_real_path()
    html_dir = "data"
    return join_helper(root_dir, html_dir, requested_path)


def html_file_real_path(requested_path: str = None) -> str:
    root_dir = html_real_path()
    html_dir = 'file'
    return join_helper(root_dir, html_dir, requested_path)


def html_tag_real_path(requested_path: str = None) -> str:
    root_dir = html_real_path()
    html_dir = "tag"
    return join_helper(root_dir, html_dir, requested_path)


def dynamic_generated_real_path(requested_path: str = None) -> str:
    root_dir = web_real_path()
    html_dir = path.join('dynamic', 'generated')
    return join_helper(root_dir, html_dir, requested_path)


def dynamic_generated_virtual_path(requested_path: str = None) -> str:
    return path.join('dyn/gen', requested_path)
