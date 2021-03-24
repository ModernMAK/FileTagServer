import json
from http.cookies import SimpleCookie
from typing import Dict, Any, Tuple, List
from litespeed import App
from litespeed.utils import json_serial

from src.util.litespeedx import Response

FetchResponse = Tuple[List[bytes], int, Dict]


def dict_to_body(d: Dict):
    return json.dumps(d, default=json_serial).encode()


def assert_response(response: FetchResponse, body: List[bytes], code: int, headers: Dict = None):
    if isinstance(body, bytes):
        body = [body]
    headers = headers or {}
    code = int(code)
    r_body, r_code, r_headers = response
    assert r_code == code
    assert r_body == body
    for name, value in headers:
        assert name in r_headers
        assert r_headers[name] == value


def internal_fetch(url: str, method: str, body: bytes = None, method_payload: Dict = None,
                   header: Dict = None, files: Dict = None) -> FetchResponse:
    result_status: int = None
    result_headers: Dict = None

    body = body or [b'']
    method_payload = method_payload or {}
    header = header or {}
    files = files or {}

    def callback(status: str, headers):
        nonlocal result_headers
        nonlocal result_status
        num_part = status.split(" ")[0]
        result_status = int(num_part)
        result_headers = dict(headers)

    request = {
        'HEADERS': header,
        'PATH_INFO': url,
        'COOKIE': SimpleCookie(),
        'REQUEST_METHOD': method,
        method: method_payload,
        'BODY': body,
        'FILES': files,
    }

    result = App()(request, callback)
    return result, result_status, result_headers
