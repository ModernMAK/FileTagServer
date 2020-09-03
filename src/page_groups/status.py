from typing import Tuple, Dict

from litespeed import serve, register_error_page, route
from pystache import Renderer

from src import config
from src.page_groups.page_group import ServeResponse, PageGroup
from src.page_groups import pathing
from src.util.page_utils import reformat_serve

renderer = None


def initialize_module(**kwargs):
    global renderer
    renderer = Renderer(search_dirs=[config.template_path])




# hardcoded for now
def add_routes():
    route("/error/404",
          function=error_404,
          no_end_slash=True,
          methods=['GET'])
    route("/error/410",
          function=error_410,
          no_end_slash=True,
          methods=['GET'])
    route("/error/418",
          function=error_418,
          no_end_slash=True,
          methods=['GET'])
    route("/error/400",
          function=error_400,
          no_end_slash=True,
          methods=['GET'])

    route("/error/301",
          function=error_301,
          no_end_slash=True,
          methods=['GET'])
    route("/error/307",
          function=error_307,
          no_end_slash=True,
          methods=['GET'])


def serve_error(error_code, context=None, headers=None, send_code=False) -> ServeResponse:
    served = serve(pathing.Static.get_html(f"error/{error_code}.html"), headers=headers)
    payload, response, headers = reformat_serve(renderer, served, context)
    if send_code:
        response = error_code
    return payload, response, headers


@register_error_page(code=404)
def error_404(request, *args, **kwargs):
    return serve_error(404)


@register_error_page(code=410)
def error_410(request, *args, **kwargs):
    return serve_error(410)


@register_error_page(code=418)
def error_418(request, *args, **kwargs):
    return serve_error(418)


@register_error_page(code=400)
def error_400(request, *args, **kwargs):
    return serve_error(400)



def error_3XX(code:int, location:str) -> ServeResponse:
    return serve_error(code,
                       context={'path': location},
                       headers={'Location': location},
                       send_code=True)

def error_301(request, *args, **kwargs) -> ServeResponse:
    new_location = kwargs['location']


def error_307(request, *args, **kwargs) -> ServeResponse:
    new_location = kwargs['location']
    return serve_error(307,
                       context={'path': new_location},
                       headers={'Location': new_location},
                       send_code=True)
