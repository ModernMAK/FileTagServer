import json
from enum import Enum

# from os.path import join
from inspect import signature
from typing import Callable, Dict, Any, Tuple, List, Union, Optional, Set, Type, ForwardRef, Mapping, AbstractSet

IntStr = Union[int,str]
MappingIntStrAny = Mapping[IntStr,Any]
AbstractSetIntStr = AbstractSet[IntStr]
DictStrAny = Dict[str,Any]

def url_join(*parts: str):
    return "/".join(parts)



# STOLEN FROM https://stackoverflow.com/questions/19022868/how-to-make-dictionary-read-only-in-python
from litespeed import route, start_with_args
from pydantic import BaseModel, Field, validate_arguments, parse_obj_as


class Util:
    ListOrModel = Union[List[BaseModel], BaseModel]
    ListOrDictStrAny = Union[List['DictStrAny'], 'DictStrAny']

    @staticmethod
    def copy(
            self: ListOrModel,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            update: 'DictStrAny' = None,
            deep: bool = False,
    ) -> ListOrModel:
        def do_copy(m: BaseModel):
            return m.copy(include=include, exclude=exclude, update=update, deep=deep)

        if isinstance(self, list):
            return [do_copy(t) for t in self]
        return do_copy(self)

    @staticmethod
    def dict(
            self: ListOrModel,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            by_alias: bool = False,
            skip_defaults: bool = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
    ) -> ListOrDictStrAny:
        def do_dict(m: BaseModel) -> DictStrAny:
            return m.dict(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults,
                          exclude_unset=exclude_unset, exclude_none=exclude_none)

        if isinstance(self, list):
            return [do_dict(t) for t in self]
        return do_dict(self)

    @staticmethod
    def json(
            self: ListOrModel,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            by_alias: bool = False,
            skip_defaults: bool = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            encoder: Optional[Callable[[Any], Any]] = None,
            **dumps_kwargs: Any,
    ) -> str:
        def do_json(m: BaseModel) -> str:
            return m.json(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults,
                          exclude_defaults=exclude_defaults, exclude_unset=exclude_unset, exclude_none=exclude_none,
                          encoder=encoder, **dumps_kwargs)

        # A hack; could use dict and then pump that into jsonbut I don't know if that will work with custom encoders
        if isinstance(self, list):
            json_list = [json.loads(do_json(t)) for t in self]
            return json.dumps(json_list, **dumps_kwargs)
        else:
            return do_json(self)


class ReadOnlyDict(dict):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("Cannot modify ReadOnlyDict")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    del __readonly__


class APISchema:
    from inspect import signature
    def __init__(self, func):
        self.func = func
        print(signature(func))

    def response(self, response: Type):
        print(response)


# Should always be get_path(*args,**kwargs):
# keyword variables can be placed before *args
# get_path(id:str,*args,**kwargs)

# StarArgs = Tuple[Any,...]
# PathSignature = Callable[[Union[List[Any,...], StarArgs], Dict[str, Any]], str]
# MethodSignature = Callable[[Request,StarArgs], Response]

class Tag(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    count: Optional[int] = 0


class File(BaseModel):
    id: int
    file: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Tag]] = Field(default_factory=lambda: [])


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
        for func, methods in self.methods.reverse_lookup().items():
            route(url, methods, func, cors_methods=cors.get(func, None), **route_kwargs)

    @property
    def methods(self) -> Methods:
        return self.__methods


@Endpoint
def files(*args, **kwargs):
    return f'files'


@files.endpoint
def file(*args, **kwargs):
    return kwargs.get('file_id', '{file_id}')


@file.endpoint
def file_tags(*args, **kwargs):
    return 'tags'


# @file.methods.get
# @validate_arguments
# def file_get(request: Dict[str, Any], id: int) -> Dict:
#     return {}


# @endpoint
# def path():
#     return '/'


# @APISchema
@files.methods.get
@validate_arguments
def files_get(request) -> List[File]:
    test_files = [File(id=1, file='example.text'), File(id=2, file='test.text'),
                  File(id=3, file='tutorial.text', tags=[Tag(id=1, name='test')])]
    include_keys = {'id': ..., 'tags': {'__all__': {'id', 'name'}}}

    a = test_files
    print(a)
    print(include_keys)
    b = [t.copy(include=include_keys) for t in a]

    def complex_print(i):
        strs = [j.dict() for j in i]
        return json.dumps(strs)

    print(f"A: {a}")
    print(f"A2: {complex_print(a)}")
    print(f"B: {b}")
    print(f"B2: {complex_print(b)}")
    return b


print("H")
print(files_get(None))


@file.methods.get
@validate_arguments
def file_get(request, id: int):
    return f'file {id}'


@file_tags.methods.get
@validate_arguments
def file_tags_get(request, id: int):
    return f'file {id} tags'


path_args = {'file_id': "(\d+)"}
route_args = {'no_end_slash': True}

files.route(path_args, route_args)
file.route(path_args, route_args)
file_tags.route(path_args, route_args)

print(files.path(**path_args))
print(file.path(**path_args))
print(file_tags.path(**path_args))
print(f'allowed: {file.methods.allowed}')
print(f'methods: {file.methods.lookup()}')
print(f'rev methods: {file.methods.reverse_lookup()}')
print(File.schema())
start_with_args()
