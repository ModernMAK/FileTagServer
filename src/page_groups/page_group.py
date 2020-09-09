from functools import partial
from typing import Dict, Tuple, Any, Callable
from litespeed import route

ServeResponse = Tuple[bytes, int, Dict[str, str]]
ServeFunction = Callable[[Any, Any], ServeResponse]


class PageGroup:
    @classmethod
    def add_routes(cls):
        raise NotImplementedError

    @classmethod
    def initialize(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def as_route_func(cls, func: ServeFunction):
        return partial(func)

    @classmethod
    def _add_route(cls, url, function, no_end_slash=True, methods=None, **kwargs):
        # Wrap the main routes for IDE's to easily read
        kwargs['url'] = url
        kwargs['no_end_slash'] = no_end_slash
        kwargs['methods'] = methods
        # The IMPORTANT PART
        # Class's functions cant be routed so we wrap it in a partial
        kwargs['function'] = partial(function)
        # We use kwargs to allow us to use any additional functionality of route
        route(**kwargs)
