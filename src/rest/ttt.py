from enum import Enum
from typing import Callable, Dict, Any, Tuple, List, Union


# STOLEN FROM https://stackoverflow.com/questions/19022868/how-to-make-dictionary-read-only-in-python
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


# Should always be get_path(*args,**kwargs):
# keyword variables can be placed before *args
# get_path(id:str,*args,**kwargs)

# StarArgs = Tuple[Any,...]
# PathSignature = Callable[[Union[List[Any,...], StarArgs], Dict[str, Any]], str]
# MethodSignature = Callable[[Request,StarArgs], Response]


class HTTPMethod(Enum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'

    def __str__(self):
        return self.value

    def __repr__(self):
        return 'HTTPMethod' + "." + self.value


class endpoint(object):
    def __init__(self, fpath=None, fget=None, fput=None, fpatch=None, fpost=None, fdelete=None):
        self.fpath = fpath
        self.__fmethods = {
            HTTPMethod.GET: fget,
            HTTPMethod.PATCH: fpatch,
            HTTPMethod.POST: fpost,
            HTTPMethod.PUT: fput,
            HTTPMethod.DELETE: fdelete,
        }

    @property
    def allowed(self) -> List[HTTPMethod]:
        return [name for name, method in self.__fmethods.items() if method is not None]

    @property
    def methods(self) -> Dict[HTTPMethod, Any]:
        return ReadOnlyDict(self.__fmethods)

    def __set_method(self, method, func):
        self.__fmethods[method] = func
        return func

    def get(self, func):
        return self.__set_method(HTTPMethod.GET, func)

    def put(self, func):
        return self.__set_method(HTTPMethod.PUT, func)

    def post(self, func):
        return self.__set_method(HTTPMethod.POST, func)

    def patch(self, func):
        return self.__set_method(HTTPMethod.PATCH, func)

    def delete(self, func):
        return self.__set_method(HTTPMethod.DELETE, func)

path = endpoint()


# @endpoint
# def path():
#     return '/'


@path.get
def a():
    return 'a'


@path.post
@path.delete
def b():
    return 'b'


print(path)
print(a)
print(b)
print(f'allowed: {path.allowed}')
print(f'methods: {path.methods}')
print(f'Is Get Allowed?: {"GET" in path.methods}')
# class EndPoint(object):
#     def __init__(self, get=None, post=None, put=None, patch=None, delete=None):
#         self._get = get
#         self._post = post
#         self._put = put
#         self._patch = patch
#         self._delete = delete
#
#     @property
#     def get(self):
#         return self._get
#
#     @get.setter
#     def get(self, value):
#         self._get = value
#
#
#     @property
#     def post(self):
#         return self._get
#
#     @post.setter
#     def post(self, value):
#         self._get = value
#
#
# def mydecorator(func):
#     return EndPoint(func)
#
#
# @mydecorator
# def a():
#     pass
#
#
# @a.post
# def b():
#     pass
