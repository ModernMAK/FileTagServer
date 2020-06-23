import os.path as path


# These should not be used to output to the html files
# Routes should be used to point to Access Points

def project_root() -> str:
    return path.dirname(path.dirname(__file__))


def html_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web/html"
    return path.join(root_dir, html_dir, requested_path)


def css_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web/css"
    return path.join(root_dir, html_dir, requested_path)


def js_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web/js"
    return path.join(root_dir, html_dir, requested_path)


def media_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web/media"
    return path.join(root_dir, html_dir, requested_path)


def image_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web/media/images"
    return path.join(root_dir, html_dir, requested_path)


def data_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "web/data"
    return path.join(root_dir, html_dir, requested_path)
