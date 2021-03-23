from functools import partial

from litespeed import serve, route
from typing import Dict, Any, Tuple, Optional
from pystache import renderer

Request = Dict[str, Any]
Response = Tuple[bytes, int, Dict[str, str]]


def render(renderer: renderer, file: str, cache_age: int = 0, headers: Optional[Dict[str, str]] = None,
           status_override: int = None, range: str = None, max_bytes_per_request: int = None, context: Dict = None):
    if context is None:
        context = {}
    content, status, header = serve(file, cache_age, headers, status_override, range, max_bytes_per_request)
    fixed_content = renderer.render(content, context)
    return fixed_content, status, header


def multiroute(url: str, no_end_slash=True, get=None, post=None, put=None, patch=None, delete=None, wrap_funcs=False,
               **kwargs):
    table = {}
    if get is not None:
        table["GET"] = get if not wrap_funcs else partial(get)
    if post is not None:
        table["POST"] = post if not wrap_funcs else partial(post)
    if put is not None:
        table["PUT"] = put if not wrap_funcs else partial(put)
    if patch is not None:
        table["PATCH"] = patch if not wrap_funcs else partial(patch)
    if delete is not None:
        table["DELETE"] = delete if not wrap_funcs else partial(delete)

    def switch(request, *args, **keywargs):
        method = request['REQUEST_METHOD']
        if method in table:
            return table[method](request, *args, **keywargs)
        else:
            return 405

    kwargs['url'] = url
    kwargs['no_end_slash'] = no_end_slash
    kwargs['methods'] = list(table.keys())
    kwargs['function'] = switch
    route(**kwargs)


class JSend:
    @staticmethod
    def raw(status: str, data: Any = None, code: int = None, message: str = None):
        response = {'status': status}
        if data is not None:
            response['data'] = data
        if code is not None:
            response['code'] = code
        if message is not None:
            response['message'] = message
        return response

    @staticmethod
    def success(data: Any) -> Dict:
        return JSend.raw("success", data)

    @staticmethod
    def fail(data: Any) -> Dict:
        return JSend.raw("fail", data)

    @staticmethod
    def error(message: str, code: int = None, **data) -> Dict:
        return JSend.raw("error", data, code, message)
