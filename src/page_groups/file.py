from typing import Dict, Any, Union, List

from litespeed import serve, route
from pystache import Renderer

from FileTagServer import config
from src.page_groups import routing, static
from src.page_groups.common import PaginationUtil
from src.page_groups.shared_page_util import get_navbar_context
from src.util.litespeedx import Response, Request
from src.util.page_utils import reformat_serve
import FileTagServer.DBI.file.old_file as file_api

renderer: Renderer = Renderer(search_dirs=[config.template_path])


def add_search_support(tags: List):
    for tag in tags:
        safe_name: str = tag['name']
        safe_name = safe_name.replace(" ", "_")
        tag['search_support'] = {
            'search_id': "search",
            'js_name': safe_name,  # '"",
        }


__files_list = "/web/files"
__file_page_sans_id = "/web/files/"
__file_page = fr"{__file_page_sans_id}(\d+)"
__file_data = fr"{__file_page}/data"


def __get_file_page(id: int):
    id = str(id)
    return __file_page_sans_id + id


def __get_file_data_page(id: int):
    id = str(id)
    return __file_page_sans_id + id + "/data"


@route(url=__files_list, no_end_slash=True, methods=["GET"])
def files_list_page(request: Request) -> Response:
    FIRST_PAGE = 0
    GET = request['GET']
    page = int(GET.get('page', 1)) - 1  # Assume page is [1,Infinity), map to [0,Infinity)
    PAGE_SIZE = 50
    PAGE_NEIGHBORS = 4

    search = GET.get("search", None)
    total_files = 3  # ApiPageGroup.get_file_count_internal(search=search)
    total_pages = PaginationUtil.get_page_count(PAGE_SIZE, total_files)
    # file_list = ApiPageGroup.get_file_list(page=page, size=PAGE_SIZE, search=search)
    files = [dict(f) for f in file_api.get_files()]
    tags = [dict(t) for t in file_api.get_files_tags()]
    tags.sort(key=lambda x: (-x['count'], x['name']))
    tag_lookup = {t['id']: t for t in tags}

    for file in files:
        f_id = file['id']
        file['url'] = __get_file_data_page(f_id)
        file['page'] = __get_file_page(f_id)
        if file['tags']:
            file_tags = file['tags'].split(",")
            file['tags'] = [tag_lookup[int(id)] for id in file_tags]
            file['tags'].sort(key=lambda x: x['name'])  # Sort tags by name
        else:
            file['tags'] = []

    serve_file = static.html.resolve_path("file/list.html")
    result = serve(serve_file)

    def pagination_url_gen(id: int):
        return routing.FilePage.get_index_list(page=id + 1, search=GET.get('search'), size=GET.get('size'))

    add_search_support(tags)
    context = {
        'page_title': "Files",
        'results': files,
        'tags': tags,
        'navbar': get_navbar_context(active=routing.FilePage.root),
        'subnavbar': {'list': 'active'},
        'pagination': PaginationUtil.get_pagination(page, total_pages, PAGE_NEIGHBORS, pagination_url_gen),
        'search_action': routing.FilePage.index_list,
        'search': search or ''
    }
    return reformat_serve(renderer, result, context)


def append_file_previews(file_list: Union[List[Dict[Any, Any]], Dict[Any, Any]]):
    if not isinstance(file_list, list):
        file_list = [file_list]
    for file in file_list:
        mime: str = file['mime']
        if mime is None:
            continue
        mime_parts = mime.split("/")
        file['preview'] = {mime_parts[0]: file}  # specify preview as type:self


@route(url=__file_page, no_end_slash=True, methods=["GET"])
def file_page(request: Request, id: int) -> Response:
    id = int(id)
    file = dict(file_api.get_file(id))
    tags = [dict(t) for t in file_api.get_file_tags(id)]
    file['tags'] = tags
    file['tags'].sort(key=lambda x: (-x['count'], x['name']))
    file['url'] = __get_file_data_page(id)
    append_file_previews(file)
    # cls.specify_edit_page(file)

    serve_file = static.html.resolve_path("file/page.html")
    result = serve(serve_file)
    context = {
        'result': file,
        'tags': file['tags'],
        'navbar': get_navbar_context(),
        'subnavbar': {}
    }
    return reformat_serve(renderer, result, context)


@route(url=__file_data, no_end_slash=True, methods=["GET"])
def file_data(request: Request, id: int) -> Response:
    range = request['HEADERS'].get('Range')
    return file_api.get_file_bytes(id, range)
#
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
