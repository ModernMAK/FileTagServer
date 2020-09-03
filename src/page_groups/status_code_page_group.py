from litespeed import serve, register_error_page
from pystache import Renderer

from src import config
from src.page_groups import pathing
from src.page_groups.page_group import ServeResponse, ServeFunction
from src.util.page_utils import reformat_serve
# HELPER import
from http import HTTPStatus


class StatusPageGroup:
    renderer = None

    @classmethod
    def serve_error(cls, error_code, context=None, headers=None, send_code=False) -> ServeResponse:
        served = serve(pathing.Static.get_html(f"error/{error_code}.html"), headers=headers)
        payload, response, headers = reformat_serve(cls.renderer, served, context)
        if send_code:
            response = error_code
        return payload, response, headers

    @classmethod
    def _serve_error_as_route_func(cls, error_code) -> ServeFunction:
        def __internal(request, *args, **kwargs):
            return cls.serve_error(error_code)

        return __internal

    @classmethod
    def add_routes(cls):
        codes = [400, 404, 410, 418]
        for code in codes:
            register_error_page(code=code,
                                function=cls._serve_error_as_route_func(code))

    @classmethod
    def initialize(cls, **kwargs):
        cls.renderer = Renderer(search_dirs=[config.template_path])

    @classmethod
    def serve_redirect(cls, code: int, location: str) -> ServeResponse:
        return cls.serve_error(code,
                               context={'path': location},
                               headers={'Location': location},
                               send_code=True)
