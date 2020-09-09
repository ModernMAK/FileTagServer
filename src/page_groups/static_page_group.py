from typing import Callable

from litespeed import route, serve
from src.page_groups.page_group import PageGroup, ServeResponse, ServeFunction
from src.page_groups import routing, pathing


class StaticGroup(PageGroup):
    # serves the file; using the path function to resolve the full path
    @staticmethod
    def __serve_path_func(path_func: Callable[[str], str]) -> ServeFunction:
        def __internal(request, path: str) -> ServeResponse:
            print(path_func(path))
            return serve(path_func(path))

        return __internal

    @classmethod
    def add_routes(cls):
        # capture everything after our text
        capture_regex = "(.*)"
        route(
            routing.Static.get_css(capture_regex),
            function=cls.__serve_path_func(pathing.Static.get_css),
            no_end_slash=True,
            methods=['GET'])

        route(routing.Static.get_javascript(capture_regex),
              function=cls.__serve_path_func(pathing.Static.get_javascript),
              no_end_slash=True,
              methods=['GET'])

        route(routing.Static.get_image(capture_regex),
              function=cls.__serve_path_func(pathing.Static.get_image),
              no_end_slash=True,
              methods=['GET'])

    @classmethod
    def initialize(cls, **kwargs):
        pass
