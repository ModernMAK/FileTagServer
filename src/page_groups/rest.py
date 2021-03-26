from typing import Dict, Any, Union, List

from litespeed import serve, route
from pystache import Renderer

from src import config
from src.page_groups import routing, static
from src.page_groups.common import PaginationUtil
from src.page_groups.shared_page_util import get_navbar_context
from src.util.litespeedx import Response, Request
from src.util.page_utils import reformat_serve
import src.api.file as file_api

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
                "/api/files/<b>:id</b>", __file,
                get=__file + "#GET", put=__file + "#PUT", patch=__file + "#PATCH", delete=__file + "#DELETE",
                methods=[
                    build_api_doc_method("Get File", __file + "#GET", "GET"),
                    build_api_doc_method("Set File Info", __file + "#PUT", "PUT"),
                    build_api_doc_method("Modify File Info", __file + "#PATCH", "PATCH"),
                    build_api_doc_method("Delete File", __file + "#DELETE", "DELETE"),
                ]),
            build_api_doc(
                "/api/file/<b>:id</b>/tags", __file_tags,
                get=__file + "#GET", put=__file + "#PUT", post=__file + "#POST", delete=__file + "#DELETE",
                methods=[
                    build_api_doc_method("Get File Tags", __file_tags + "#GET", "GET"),
                    build_api_doc_method("Add Tags", __file_tags + "#POST", "POST"),
                    build_api_doc_method("Set File Tags", __file_tags + "#PUT", "PUT"),
                    build_api_doc_method("Delete Tags", __file_tags + "#DELETE", "DELETE"),
                ]),
            build_api_doc(
                "/api/file/<b>:id</b>/data", __file_data,
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
                "/api/tags/<b>:id</b>", __tag,
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


def __build_method_cards_context(get=None, post=None, put=None, patch=None, delete=None):
    __allowed_methods_lookup = {'GET': get, 'POST': post, 'PUT': put, 'PATCH': patch, 'DELETE': delete}
    __allowed_methods: List[str] = [key for key, value in __allowed_methods_lookup.items() if value is not None]

    r = []
    for m in __allowed_methods:
        d = {
            'id': m,
            'method_lower': m.lower(),
            'method_upper': m,
            'method_links': __build_method_card_footer_context(m, __allowed_methods)
        }
        d.update(__allowed_methods_lookup[m])
        r.append(d)
    return r, __allowed_methods


def __build_method_card_footer_context(current: str, allowed: List[str], force_outline=False, force_filled=False):
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
        d = {
            'method': m.lower(),
            'text': m.upper(),
            'href': "#" + m.upper(),
            'allowed': is_allowed,
            'disabled': is_current or not is_allowed,
            'outline': (not is_allowed or not force_filled) and (force_outline or not is_allowed or not is_current)
        }
        r.append(d)
    return r


@route(url=__file, no_end_slash=True, methods=["GET"])
def file(request: Request):
    __file_schema, __allowed_methods = __build_method_cards_context(
        get={'description': "Retrieves the specified file.",
             'arguments': [{'name': 'fields', 'type': 'List[string]', 'optional': True,
                            'description': 'List of fields to return from the resource.',
                            'values': 'See File Model for valid values. See Requests for formatting a string list.'}],
             'has_arguments': True,
             },
        put={
            'description': "Sets file information for the specified file. All arguments must be provided. To perform a partial update, see #PATCH.",
            'arguments': [
                {'name': 'name', 'type': 'str', 'optional': False, 'description': 'Name of the file.', },
                {'name': 'path', 'type': 'str', 'optional': False, 'description': 'Path/URL of the file.', },
                {'name': 'mime', 'type': 'str', 'optional': False, 'description': 'Mimetype of the file.', },
                {'name': 'description', 'type': 'str', 'optional': False, 'description': 'The file\'s description.', }
            ],
            'has_arguments': True, },
        patch={
            'description': "Updates file information for the specified file. Omitted arguments are not updated. To perform a full update, see #PUT.",
            'arguments': [
                {'name': 'name', 'type': 'str', 'optional': True, 'description': 'Name of the file.'},
                {'name': 'path', 'type': 'str', 'optional': True, 'description': 'Path/URL of the file.', },
                {'name': 'mime', 'type': 'str', 'optional': True, 'description': 'Mimetype of the file.', },
                {'name': 'description', 'type': 'str', 'optional': True, 'description': 'The file\'s description.', }],
            'has_arguments': True,
        },
        delete={'description': "Deletes the given file"},
    )

    serve_file = static.html.resolve_path("api/page.html")
    result = serve(serve_file)
    context = {
        'route': {
            'url': '/api/files/<b>{id}</b>',
            'description': 'Exposes operations on a File Resource.',
            'arguments': [{'name': 'id', 'type': 'integer', 'description': 'The ID of the file.'}],
            'method_links': __build_method_card_footer_context(None, __allowed_methods, force_filled=True),
            'has_arguments': True,
        },
        'schema': __schema,
        'methods': __file_schema,
        'navbar': get_navbar_context(),
        'subnavbar': {}
    }
    return reformat_serve(renderer, result, context)

#
# class FilePageGroup(PageGroup):
#     renderer = None
#
#     @classmethod
#     def add_routes(cls):
#         get_only = ['GET']
#         post_only = ['POST']
#         # TODO move this to startup
#         cls._add_route(routing.WebRoot.root, function=cls.index, methods=get_only)
#
#         cls._add_route(routing.FilePage.root, function=cls.index, methods=get_only)
#
#         cls._add_route(routing.FilePage.index_list, function=cls.view_as_list, methods=get_only)
#
#         cls._add_route(routing.FilePage.view_file, function=cls.view_file, methods=get_only)
#
#         cls._add_route(routing.FilePage.edit_file, function=cls.handle_edit, methods=['GET', 'POST'])
#
#         cls._add_route(routing.FilePage.serve_file_raw, function=cls.serve_raw_file, methods=get_only)
#         cls._add_route(routing.FilePage.serve_page_raw, function=cls.serve_raw_page, methods=get_only)
#
#         cls._add_route(routing.FilePage.slideshow, function=cls.serve_slideshow, methods=get_only)
#
#     @classmethod
#     def initialize(cls, **kwargs):
#         cls.renderer = Renderer(search_dirs=[config.template_path])
#
#     #########
#     # Displays the primary page of the file page group
#     # This should almost always either be;
#     #   A splash-screen main page for the group
#     #   A homepage for the topics of the group
#     #   An alias for primary page of the group (deferring to that page display)
#     #########
#     @classmethod
#     def index(cls, request: Dict[str, Any]) -> ServeResponse:
#         print("file page index")
#         return StatusPageGroup.serve_redirect(301, routing.FilePage.index_list)
#         # return cls.view_as_list(request)
#
#     @staticmethod
#     def append_file_previews(file_list: Union[List[Dict[Any, Any]], Dict[Any, Any]]):
#         if not isinstance(file_list, list):
#             file_list = [file_list]
#         for file in file_list:
#             mime: str = file['mime']
#             mime_parts = mime.split("/")
#             file['preview'] = {mime_parts[0]: file}  # specify preview as type:self
#
#     @classmethod
#     def add_search_support(cls, tags: List):
#         for tag in tags:
#             safe_name: str = tag['name']
#             safe_name = safe_name.replace(" ", "_")
#             tag['search_support'] = {
#                 'search_id': "search",
#                 'js_name': safe_name,  # '"",
#             }
#
#     #########
#     # Displays the files in the file_page database as a list
#     # This is primarily intended to be used to edit multiple file's tags at once
#     # GET SUPPORT:
#     #   Pagination ~ Page # Only => 'page'
#     #       page counts from 1; to reflect the UI
#     #########
#     @classmethod
#     def view_as_list(cls, request: Dict[str, Any]) -> ServeResponse:
#         FIRST_PAGE = 0
#         GET = request['GET']
#         page = int(GET.get('page', 1)) - 1  # Assume page is [1,Infinity), map to [0,Infinity)
#         PAGE_SIZE = 50
#         PAGE_NEIGHBORS = 4
#
#         search = GET.get("search", None)
#         total_files = ApiPageGroup.get_file_count_internal(search=search)
#         total_pages = PaginationUtil.get_page_count(PAGE_SIZE, total_files)
#         # # Determine if page is valid
#         # if not PaginationUtil.is_page_valid(page, page_size, file_count) and page != FIRST_PAGE:
#         #     return StatusPageGroup.serve_error(404)
#
#         file_list = ApiPageGroup.get_file_list(page=page, size=PAGE_SIZE, search=search)
#
#         # Get unique tags
#         unique_tags = {}
#         for file in file_list:
#             for tag in file['tags']:
#                 if tag['id'] not in unique_tags:
#                     unique_tags[tag['id']] = tag
#         # Convert to list & Sort
#         tag_list = [v for v in unique_tags.values()]
#         tag_list.sort(key=lambda x: (-x['count'], x['name']))
#
#         for file in file_list:
#             file['tags'].sort(key=lambda x: x['name'])  # Sort tags by name
#
#         serve_file = pathing.Static.get_html("file/list.html")
#         result = serve(serve_file)
#
#         def pagination_url_gen(id: int):
#             return routing.FilePage.get_index_list(page=id + 1, search=GET.get('search'), size=GET.get('size'))
#
#         cls.add_search_support(tag_list)
#         context = {
#             'page_title': "Files",
#             'results': file_list,
#             'tags': tag_list,
#             'navbar': get_navbar_context(active=routing.FilePage.root),
#             'subnavbar': {'list': 'active'},
#             'pagination': PaginationUtil.get_pagination(page, total_pages, PAGE_NEIGHBORS, pagination_url_gen),
#             'search_action': routing.FilePage.index_list,
#             'search': search if search is not None else ''
#
#         }
#         return reformat_serve(cls.renderer, result, context)
#
#     #########
#     # Displays the files in the file_page database as a list
#     # This is primarily intended to be used to edit multiple file's tags at once
#     # GET SUPPORT:
#     #   Pagination ~ Page # Only => 'page'
#     #       page counts from 1; to reflect the UI
#     #########
#     @classmethod
#     def view_file(cls, request: Dict[str, Any]) -> ServeResponse:
#         file = ApiPageGroup.get_file_internal(request['GET'].get('id'))
#
#         file['tags'].sort(key=lambda x: (-x['count'], x['name']))
#
#         cls.append_file_previews(file)
#         cls.specify_edit_page(file)
#
#         serve_file = pathing.Static.get_html("file/page.html")
#         result = serve(serve_file)
#         context = {
#             'result': file,
#             'tags': file['tags'],
#             'navbar': get_navbar_context(),
#             'subnavbar': {}
#         }
#         return reformat_serve(cls.renderer, result, context)
#
#     @classmethod
#     def handle_edit(cls, request: Dict[str, Any]) -> ServeResponse:
#         method = request['REQUEST_METHOD']
#         if method == "POST":
#             return cls.view_file_edit_action(request)
#         elif method == "GET":
#             return cls.view_file_edit(request)
#         else:
#             return 405
#
#     @classmethod
#     def view_file_edit(cls, request: Dict[str, Any]) -> ServeResponse:
#         file = ApiPageGroup.get_file_internal(request['GET'].get('id'))
#         file['tags'].sort(key=lambda x: (x['name']))
#
#         cls.append_file_previews(file)
#         cls.specify_edit_page(file)
#         serve_file = pathing.Static.get_html("file/page_edit.html")
#         result = serve(serve_file)
#         context = {
#             'result': file,
#             'tags': file['tags'],
#             'navbar': get_navbar_context(),
#             'subnavbar': {},
#             'form': {
#                 'action': routing.FilePage.edit_file,
#                 'id': file['id']
#             }
#         }
#         return reformat_serve(cls.renderer, result, context)
#
#     @classmethod
#     def view_file_edit_action(cls, request: Dict[str, Any]) -> ServeResponse:
#         print(request)
#         POST = request['POST']
#         file_id = POST['id']
#         tags: str = POST['tags']
#         tag_list = tags.splitlines()
#         tag_list = [tag.strip() for tag in tag_list]
#
#         missing_tags = ApiPageGroup.get_valid_tags(tag_list, True)
#         missing_tags_values = [(tag['name'], "") for tag in missing_tags]
#         if len(missing_tags) > 0:
#             ApiPageGroup.api.tag.insert(missing_tags_values)
#         tag_ids: List[Union[str, int]] = [tag['id'] for tag in ApiPageGroup.get_valid_tags(tag_list)]
#
#         update_args = {}
#
#         def try_add(names: List[str], source: Dict, dest: Dict):
#             for name in names:
#                 if name in source:
#                     dest[name] = source[name]
#
#         try_add(['name', 'description'], POST, update_args)
#         update_args['tags'] = tag_ids
#
#         ApiPageGroup.update_file_info_internal(file_id, **update_args)
#         return StatusPageGroup.serve_submit_redirect(routing.FilePage.get_edit_file(id=file_id))
#
#     @classmethod
#     def serve_raw_file(cls, request: Dict[str, Any]) -> ServeResponse:
#         file_id = request.get('GET').get('id')
#         client = dbapi.MasterClient(db_path=config.db_path)
#         results = client.file.fetch(ids=[file_id])
#         if len(results) == 0:
#             return StatusPageGroup.serve_error(404)
#         else:
#             return serve(results[0]['path'], range=request.get("range", "bytes=0-"))
#
#     @classmethod
#     def serve_raw_page(cls, request: Dict[str, Any]) -> ServeResponse:
#         file_id = request.get('GET').get('id')
#         client = dbapi.MasterClient(db_path=config.db_path)
#         results = client.file.fetch(ids=[file_id])
#         if len(results) == 0:
#             return StatusPageGroup.serve_error(404)
#         else:
#             result = results[0]
#             # print(result)
#             mime = result['mime']
#             # print(mime)
#             # .split("/")[0]
#             mime = mime.split("/")
#             if len(mime) > 0:
#                 mime = mime[0]
#             else:
#                 mime = ""
#
#             raw_url = routing.FilePage.get_serve_file_raw(result['id'])
#             if mime == "image":
#                 serve_file = pathing.Static.get_html("raw/image.html")
#                 ctx = {
#                     "title": result['name'],
#                     "source": raw_url
#                 }
#                 s = serve(serve_file)
#                 return reformat_serve(cls.renderer, s, ctx)
#             else:
#                 return StatusPageGroup.serve_error(404)
#
#     @classmethod
#     def serve_slideshow(cls, request: Dict[str, Any]) -> ServeResponse:
#         file_id = request.get('GET').get('id')
#         client = dbapi.MasterClient(db_path=config.db_path)
#         results = client.file.fetch(ids=[file_id])
#         if len(results) == 0:
#             return StatusPageGroup.serve_error(404)
#         else:
#             result = results[0]
#             mime = result['mime'].split("/")
#             if len(mime) > 0:
#                 mime = mime[0]
#             else:
#                 mime = ""
#
#             raw_url = routing.FilePage.get_serve_file_raw(result['id'])
#             serve_file = pathing.Static.get_html("file/ss.html")
#             if mime == "image":
#                 ctx = {
#                     "title": result['name'],
#                     "image": {
#                         "alt": result['description'],
#                         "source": raw_url
#                     }
#                 }
#                 s = serve(serve_file)
#                 return reformat_serve(cls.renderer, s, ctx)
#             elif mime == "video":
#                 ctx = {
#                     "title": result['name'],
#                     "video": {
#                         "alt": result['description'],
#                         "source": raw_url,
#                         "mime": result['mime']
#                     }
#                 }
#                 s = serve(serve_file)
#                 return reformat_serve(cls.renderer, s, ctx)
#             else:
#                 return StatusPageGroup.serve_error(404)
#
#     @classmethod
#     def specify_edit_page(cls, file):
#         file['edit_page'] = routing.full_path(routing.FilePage.get_edit_file(file['id']))
