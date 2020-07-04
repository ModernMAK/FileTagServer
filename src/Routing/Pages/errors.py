from typing import Tuple, Dict

from litespeed import register_error_page, serve
from pystache import Renderer

from src import PathUtil
from src.Routing.Pages.page_utils import reformat_serve

renderer = None


def initialize_module(**kwargs):
    global renderer
    config = kwargs.get('config', {})
    launch_args = config.get('Launch Args', {})
    search_dirs = launch_args.get('template_dirs', [PathUtil.html_real_path("templates")])
    renderer = Renderer(search_dirs=search_dirs)


# hardcoded for now
def add_routes():
    pass


def serve_error(error_path, context=None) -> Tuple[bytes, int, Dict[str, str]]:
    served = serve(PathUtil.html_real_path(f"error/{error_path}.html"))
    return reformat_serve(renderer, served, context)


@register_error_page(404)
def error_404(request, *args, **kwargs):
    return serve_error(404)
