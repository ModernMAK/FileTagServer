from enum import Enum
from typing import Dict, List, Callable, Set, Any

from litespeed import route

from src.rest.common import url_join


class HTTPMethod(str, Enum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'

    # def __str__(self):
    #     return self.value
    #
    # def __repr__(self):
    #     return 'HTTPMethod' + "." + self.value


class Path(object):
    def __init__(self, func: Callable[[Any], str]):
        self.func = func

    def __call__(self, *args, **kwargs) -> str:
        return self.func(*args, **kwargs)

    def subpath(self, child) -> 'Path':
        def joined(*args, **kwargs):
            return url_join(self.func(*args, **kwargs), child(*args, **kwargs))

        return Path(joined)


class Methods(object):
    def __init__(self):
        self.__methods: Dict[HTTPMethod, Callable] = dict()
        self.__cors: Set[HTTPMethod] = set()

    def reverse_lookup(self, use_cors: bool = False) -> Dict[Callable, HTTPMethod]:
        def invert(d: Dict) -> Dict:
            o = {}
            for key, value in d.items():
                if value not in o:
                    o[value] = [key]
                else:
                    o[value].append(key)
            return o

        return invert(self.lookup(use_cors))

    # Returns a -shallow copy- dict
    def lookup(self, use_cors: bool = False) -> Dict[HTTPMethod, Callable]:
        if not use_cors:
            return dict(self.__methods)
        else:
            return {key: value for key, value in self.__methods.items() if key in self.__cors}

    def set_function(self, func, method, allow_cors: bool = False):
        if func is None:
            if method in self.__methods:
                del self.__methods[method]
        else:
            self.__methods[method] = func

        if allow_cors:
            self.__cors.add(method)
        else:
            try:
                self.__cors.remove(method)
            except KeyError:
                pass
        return func

    def get(self, func, allow_cors: bool = False):
        return self.set_function(func, HTTPMethod.GET, allow_cors)

    def put(self, func, allow_cors: bool = False):
        return self.set_function(func, HTTPMethod.PUT, allow_cors)

    def post(self, func, allow_cors: bool = False):
        return self.set_function(func, HTTPMethod.POST, allow_cors)

    def patch(self, func, allow_cors: bool = False):
        return self.set_function(func, HTTPMethod.PATCH, allow_cors)

    def delete(self, func, allow_cors: bool = False):
        return self.set_function(func, HTTPMethod.DELETE, allow_cors)

    @property
    def allowed(self) -> List[HTTPMethod]:
        return [name for name, method in self.__methods.items() if method is not None]

    @property
    def allowed_cors(self) -> List[HTTPMethod]:
        return list(self.__cors)


class Endpoint:
    def __init__(self, path: Path = None, methods: Methods = None):
        self.path = path if isinstance(path, Path) else Path(path)
        self.__methods = methods or Methods()

    def resolve_path(self, **kwargs) -> str:
        return self.path(**kwargs)

    def endpoint(self, nested_path) -> 'Endpoint':
        return Endpoint(self.path.subpath(nested_path))

    def route(self, path_kwargs: Dict = None, route_kwargs: Dict = None):
        # merges shared functions
        path_kwargs = path_kwargs or {}
        route_kwargs = route_kwargs or {}

        url = self.path(**path_kwargs)
        cors = self.methods.reverse_lookup(True)
        if len(self.methods.allowed) == 0:
            print(f"WARNING: No methods provided for '{url}', is this endpoint a directory?")

        for func, methods in self.methods.reverse_lookup().items():
            route(url, methods, func, cors_methods=cors.get(func, None), **route_kwargs)

    def get(self, func, allow_cors: bool = False):
        return self.methods.get(func, allow_cors)

    def put(self, func, allow_cors: bool = False):
        return self.methods.put(func, allow_cors)

    def post(self, func, allow_cors: bool = False):
        return self.methods.post(func, allow_cors)

    def patch(self, func, allow_cors: bool = False):
        return self.methods.patch(func, allow_cors)

    def delete(self, func, allow_cors: bool = False):
        return self.methods.delete(func, allow_cors)

    @property
    def methods(self) -> Methods:
        return self.__methods
