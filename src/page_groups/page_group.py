import os
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

    @staticmethod
    def create_get_string(**kwargs) -> str:
        listed = []
        for k, v in kwargs.items():
            listed.append(f"{k}={v}")
        if len(listed) == 0:
            return ""
        return "?" + "&".join(listed)