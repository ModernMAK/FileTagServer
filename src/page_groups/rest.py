from http import HTTPStatus
from typing import Dict, List, Tuple

from litespeed import serve, route
from litespeed.error import ResponseError
from pystache import Renderer

from FileTagServer import config
from src.page_groups import static
from src.page_groups.shared_page_util import get_navbar_context
from src.util.litespeedx import Response, Request
from src.util.page_utils import reformat_serve

renderer: Renderer = Renderer(search_dirs=[config.template_path])

__root = fr"/web/api"
__files = __root + "/files"
__files_tags = __root + "/files/tags"
__files_search = __root + "/files/search"
__file = __root + "/file"
__file_tags = __root + "/file/tags"
__file_data = __root + "/file/data"
__tags = __root + "/tags"
__tag = __root + "/tag"


def build_api_doc(route, page_url, methods, **kwargs):
    d = dict(kwargs)
    r = {'url': page_url, 'text': route, 'methods': methods}
    d.update(r)
    return d


def build_api_doc_method(purpose, page_url, method):
    return {'url': page_url, 'text': purpose, 'badge': f"badge-method-{method.lower()}", 'method': method}


__schema = [
    {
        'group': "Files",
        'endpoints': [
            build_api_doc(
                "/api/files", __files,
                get=__files + "#GET", post=__files + "#POST",
                methods=[
                    build_api_doc_method("Get / Search Files", __files + "#GET", "GET"),
                    build_api_doc_method("Create File", __files + "#POST", "POST")
                ]),
            build_api_doc(
                "/api/files/tags", __files_tags,
                get=__files_tags + "#GET",
                methods=[
                    build_api_doc_method("Get Tags From Search", __files_tags + "#GET", "GET"),
                ]),
            build_api_doc(
                "/api/files/search", __files_search,
                get=__files_search + "#GET", post=__files_search + "#POST",
                methods=[
                    build_api_doc_method("Redirect Search", __files_search + "#GET", "GET"),
                    build_api_doc_method("Submit Search", __files_search + "#POST", "POST"),
                ]),
            build_api_doc(
                "/api/files/<b>{id}</b>", __file,
                get=__file + "#GET", put=__file + "#PUT", patch=__file + "#PATCH", delete=__file + "#DELETE",
                methods=[
                    build_api_doc_method("Get File", __file + "#GET", "GET"),
                    build_api_doc_method("Set File Info", __file + "#PUT", "PUT"),
                    build_api_doc_method("Modify File Info", __file + "#PATCH", "PATCH"),
                    build_api_doc_method("Delete File", __file + "#DELETE", "DELETE"),
                ]),
            build_api_doc(
                "/api/file/<b>{id}</b>/tags", __file_tags,
                get=__file + "#GET", put=__file + "#PUT", post=__file + "#POST", delete=__file + "#DELETE",
                methods=[
                    build_api_doc_method("Get File Tags", __file_tags + "#GET", "GET"),
                    build_api_doc_method("Add Tags", __file_tags + "#POST", "POST"),
                    build_api_doc_method("Set File Tags", __file_tags + "#PUT", "PUT"),
                    build_api_doc_method("Delete Tags", __file_tags + "#DELETE", "DELETE"),
                ]),
            build_api_doc(
                "/api/file/<b>{id}</b>/data", __file_data,
                get=__file_data + "#GET",
                methods=[
                    build_api_doc_method("Get File Data", __file_data + "#GET", "GET"),
                ])
        ]
    },
    {
        'group': "Tags",
        'endpoints': [
            build_api_doc(
                "/api/tags", __tags,
                get=__tags + "#GET", post=__tags + "#POST",
                methods=[
                    build_api_doc_method("Get / Search Tags", __tags + "#GET", "GET"),
                    build_api_doc_method("Create Tag", __tags + "#POST", "POST")
                ]),
            build_api_doc(
                "/api/tags/<b>{id}</b>", __tag,
                get=__tag + "#GET", put=__tag + "#PUT", patch=__tag + "#PATCH", delete=__tag + "#DELETE",
                methods=[
                    build_api_doc_method("Get Tag", __tag + "#GET", "GET"),
                    build_api_doc_method("Set Tag Info", __tag + "#PUT", "PUT"),
                    build_api_doc_method("Modify Tag Info", __tag + "#PATCH", "PATCH"),
                    build_api_doc_method("Delete Tag", __tag + "#DELETE", "DELETE"),
                ]),
        ]
    }
]


@route(url=__root, no_end_slash=True, methods=["GET"])
def index(request: Request) -> Response:
    serve_file = static.html.resolve_path("api/page_badge_all.html")
    result = serve(serve_file)
    context = {
        'schema': __schema,
        'navbar': get_navbar_context(),
        'subnavbar': {}
    }
    return reformat_serve(renderer, result, context)


def __build_method_cards_context(get=None, post=None, put=None, patch=None, delete=None) -> Tuple[
    List[Dict], List[str]]:
    __allowed_methods_lookup = {'GET': get, 'POST': post, 'PUT': put, 'PATCH': patch, 'DELETE': delete}
    __allowed_methods: List[str] = [key for key, value in __allowed_methods_lookup.items() if value is not None]

    r = []
    for m in __allowed_methods:
        d = {
            'id': m,
            'method_lower': m.lower(),
            'method_upper': m,
            'method_links': __build_method_card_footer_context(m, __allowed_methods, skip_unallowed=True,
                                                               ignore_single=True)
        }
        d.update(__allowed_methods_lookup[m])
        r.append(d)
    return r, __allowed_methods


def __build_method_card_footer_context(current: str, allowed: List[str], force_outline=False, force_filled=False,
                                       skip_unallowed=False, ignore_single=False):
    methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    r = []
    if current is not None:
        current = current.upper()
    allowed = [t.upper() for t in allowed]
    if current is not None:
        allowed.append(current)  # In case im dumb

    for m in methods:
        is_current = current is not None and m == current
        is_allowed = m in allowed
        if skip_unallowed and not is_allowed:
            continue
        d = {
            'method': m.lower(),
            'text': m.upper(),
            'href': "#" + m.upper(),
            'allowed': is_allowed,
            'disabled': is_current or not is_allowed,
            'outline': (not is_allowed or not force_filled) and (force_outline or not is_allowed or not is_current)
        }
        r.append(d)
    if ignore_single and len(r) == 1:
        return []
    return r


def __build_method_argument(name: str, type: str, description: str, optional=False):
    return {'name': name, 'type': type, 'description': description, 'optional': optional}


def __build_method_card_context(description: str, query_args: List[dict] = None, header_args: List[dict] = None,
                                responses: List[dict] = None):
    return {
        'description': description,
        'query_arguments': query_args,
        'has_query_arguments': query_args is not None,

        'header_arguments': header_args,
        'has_header_arguments': header_args is not None,

        'responses': responses,
        'has_responses': responses is not None,
    }


def __build_endpoint_card_context(url: str, description: str, allowed_methods: List[str], path_args: List[dict] = None,
                                  header_args: List[dict] = None, responses: List[dict] = None):
    return {
        'url': url,
        'description': description,

        'path_arguments': path_args,
        'has_path_arguments': path_args is not None,

        'header_arguments': header_args,
        'has_header_arguments': header_args is not None,

        'responses': responses,
        'has_responses': responses is not None,

        'method_links': __build_method_card_footer_context(None, allowed_methods, force_filled=True,
                                                           skip_unallowed=True),
    }


def __build_response_raw(type: str, data: str, description: str, code: HTTPStatus, row_type: str = None):
    return {'type': type, 'data': data, 'code': f"{code.value} {code.phrase}",
            'description': description, 'row-type': row_type or []}


def __build_response_success(data: str, description: str, code: HTTPStatus = HTTPStatus.OK):
    return __build_response_raw('success', data, description, code, 'success')


def __build_response_fail(data: str, description: str, code: HTTPStatus = HTTPStatus.BAD_REQUEST):
    return __build_response_raw('fail', data, description, code, 'warning')


def __build_response_error(data: str, description: str, code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR):
    return __build_response_raw('error', data, description, code, 'danger')


@route(url=__file, no_end_slash=True, methods=["GET"])
def file(request: Request):
    __file_schema, __allowed_methods = __build_method_cards_context(
        get=__build_method_card_context(
            "Retrieves the specified file.",
            query_args=[
                __build_method_argument('fields', 'List[string]',
                                        'List of fields to return from the resource.'
                                        '\nSee File Model for valid values.'
                                        '\nSee Requests for formatting a string list.',
                                        True)],
            responses=[
                __build_response_success('File Model', "The file was retrieved successfully."),
                __build_response_fail('Errors', "The request was invalid."),
                __build_response_error('N/A', "An internal server error occurred."),
            ]),
        put=__build_method_card_context(
            "Sets file information for the specified file. All arguments must be provided. To perform a partial update, see #PATCH.",
            query_args=[__build_method_argument('name', 'str', 'Name of the file.', False),
                        __build_method_argument('path', 'str', 'Path/URL of the file.', False),
                        __build_method_argument('mime', 'str', 'Mimetype of the file.', False),
                        __build_method_argument('description', 'str', 'The file\'s description.', False)],
            responses=[
                __build_response_success('N/A', "The file was set successfully.", HTTPStatus.NO_CONTENT),
                __build_response_fail('Errors', "The request was invalid."),
                __build_response_error('N/A', "An internal server error occurred."),
            ]),
        patch=__build_method_card_context(
            "Updates file information for the specified file. Omitted arguments are not updated. To perform a full update, see #PUT.",
            [__build_method_argument('name', 'str', 'Name of the file.', True),
             __build_method_argument('path', 'str', 'Path/URL of the file.', True),
             __build_method_argument('mime', 'str', 'Mimetype of the file.', True),
             __build_method_argument('description', 'str', 'The file\'s description.', True)],
            responses=[
                __build_response_success('N/A', "The file was updated successfully.", HTTPStatus.NO_CONTENT),
                __build_response_fail('Errors', "The request was invalid."),
                __build_response_error('N/A', "An internal server error occurred."),
            ]),
        delete=__build_method_card_context(
            "Deletes the given file",
            responses=[
                __build_response_success('N/A', "The file was deleted successfully.", HTTPStatus.NO_CONTENT),
                __build_response_error('N/A', "An internal server error occurred."),
            ])
    )
    __endpoint = __build_endpoint_card_context(
        '/api/files/<b>{id}</b>', 'Exposes operations on a File Resource.',
        __allowed_methods,
        [__build_method_argument('id', 'integer', 'The ID of the file.')],
        responses=[__build_response_fail('Errors', "The file doesn't exist.", HTTPStatus.NOT_FOUND)]
    )
    serve_file = static.html.resolve_path("api/page.html")
    result = serve(serve_file)
    context = {
        'route': __endpoint,
        'schema': __schema,
        'methods': __file_schema,
        'navbar': get_navbar_context(),
        'subnavbar': {}
    }
    return reformat_serve(renderer, result, context)


@route(url=__file_data, no_end_slash=True, methods=["GET"])
def file_data(request: Request):
    __file_schema, __allowed_methods = __build_method_cards_context(
        get=__build_method_card_context(
            "Retrieves the specified file's underlying data. This request does not return a REST response; instead serving the file directly.",
            responses=[
                __build_response_raw('N/A', 'N/A', "The bytes of the file.", HTTPStatus.OK, "success"),
                __build_response_raw('N/A', 'N/A', "The bytes of the file. If range was specified.",
                                     HTTPStatus.PARTIAL_CONTENT, "success"),
                __build_response_raw('N/A', 'N/A', "The resource exists but it's content is missing. This is typically caused by the resource being moved.",
                                     HTTPStatus.NO_CONTENT, "warning"),
                __build_response_raw('N/A', 'N/A', "An internal server error occurred.",
                                     HTTPStatus.INTERNAL_SERVER_ERROR, "danger")]
        ))
    __endpoint = __build_endpoint_card_context(
        '/api/files/<b>{id}</b>/data',
        'Exposes operations on a File\'s physical data on disk.',
        __allowed_methods,
        [__build_method_argument('id', 'integer', 'The ID of the file.')],
        responses=[__build_response_raw('N/A', 'N/A', "The file doesn't exist.", HTTPStatus.NOT_FOUND, 'warning')])
    serve_file = static.html.resolve_path("api/page.html")
    result = serve(serve_file)
    context = {
        'route': __endpoint,
        'schema': __schema,
        'methods': __file_schema,
        'navbar': get_navbar_context(),
        'subnavbar': {}
    }
    return reformat_serve(renderer, result, context)


@route(url=__file_tags, no_end_slash=True, methods=["GET"])
def file_tags(request: Request):
    raise ResponseError(HTTPStatus.NOT_IMPLEMENTED)


@route(url=__files, no_end_slash=True, methods=["GET"])
def files(request: Request):
    raise ResponseError(HTTPStatus.NOT_IMPLEMENTED)


@route(url=__files_tags, no_end_slash=True, methods=["GET"])
def files_tags(request: Request):
    raise ResponseError(HTTPStatus.NOT_IMPLEMENTED)


@route(url=__files_search, no_end_slash=True, methods=["GET"])
def files_search(request: Request):
    raise ResponseError(HTTPStatus.NOT_IMPLEMENTED)


@route(url=__tags, no_end_slash=True, methods=["GET"])
def tags(request: Request):
    raise ResponseError(HTTPStatus.NOT_IMPLEMENTED)


@route(url=__tag, no_end_slash=True, methods=["GET"])
def tags(request: Request):
    raise ResponseError(HTTPStatus.NOT_IMPLEMENTED)
