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
