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


# Preferably id move some things to a media path
def media_path(requested_path: str = None) -> str:
    raise Exception
    # root_dir = project_root()
    # html_dir = "media"
    # return path.join(root_dir, html_dir, requested_path)


def post_path(requested_path: str = None) -> str:
    root_dir = project_root()
    html_dir = "images/dynamic/posts"
    return path.join(root_dir, html_dir, requested_path)
