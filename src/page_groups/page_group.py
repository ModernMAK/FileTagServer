from functools import partial
from typing import Dict, Tuple, Any, Callable

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
