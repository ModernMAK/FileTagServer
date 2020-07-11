from typing import Tuple, Dict

from litespeed import serve, register_error_page
from pystache import Renderer

from src.routing.pages.page_utils import reformat_serve
from src.routing.virtual_access_points import RequiredVap

renderer = None


def initialize_module(**kwargs):
    global renderer
    config = kwargs.get('config', {})
    launch_args = config.get('Launch Args', {})
    search_dirs = launch_args.get('template_dirs', [RequiredVap.html_real("templates")])
    renderer = Renderer(search_dirs=search_dirs)


# hardcoded for now
def add_routes():
    pass
#     App.register_error_route(404, function=error_404)


def serve_error(error_path, context=None) -> Tuple[bytes, int, Dict[str, str]]:
    served = serve(RequiredVap.html_real(f"error/{error_path}.html"))
    return reformat_serve(renderer, served, context)


@register_error_page(code=404)
def error_404(request, *args, **kwargs):
    return serve_error(404)
