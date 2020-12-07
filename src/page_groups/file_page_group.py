from typing import Dict, Any, Union, List

from litespeed import serve
from pystache import Renderer

import src.database_api.clients  as dbapi
from src import config
from src.page_groups import pathing, routing
from src.page_groups.api_page_group import ApiPageGroup
from src.page_groups.common import PaginationUtil
from src.page_groups.page_group import PageGroup, ServeResponse
from src.page_groups.shared_page_util import get_navbar_context
from src.page_groups.status_code_page_group import StatusPageGroup
from src.util.page_utils import reformat_serve


class FilePageGroup(PageGroup):
    renderer = None

    @classmethod
    def add_routes(cls):
        get_only = ['GET']
        post_only = ['POST']
        # TODO move this to startup
        cls._add_route(routing.WebRoot.root, function=cls.index, methods=get_only)

        cls._add_route(routing.FilePage.root, function=cls.index, methods=get_only)

        cls._add_route(routing.FilePage.index_list, function=cls.view_as_list, methods=get_only)

        cls._add_route(routing.FilePage.view_file, function=cls.view_file, methods=get_only)

        cls._add_route(routing.FilePage.edit_file, function=cls.handle_edit, methods=['GET', 'POST'])

        cls._add_route(routing.FilePage.serve_file_raw, function=cls.serve_raw_file, methods=get_only)
        cls._add_route(routing.FilePage.serve_page_raw, function=cls.serve_raw_page, methods=get_only)

        cls._add_route(routing.FilePage.slideshow, function=cls.serve_slideshow, methods=get_only)

    @classmethod
    def initialize(cls, **kwargs):
        cls.renderer = Renderer(search_dirs=[config.template_path])

    #########
    # Displays the primary page of the file page group
    # This should almost always either be;
    #   A splash-screen main page for the group
    #   A homepage for the topics of the group
    #   An alias for primary page of the group (deferring to that page display)
    #########
    @classmethod
    def index(cls, request: Dict[str, Any]) -> ServeResponse:
        print("file page index")
        return StatusPageGroup.serve_redirect(301, routing.FilePage.index_list)
        # return cls.view_as_list(request)

    @staticmethod
    def append_file_previews(file_list: Union[List[Dict[Any, Any]], Dict[Any, Any]]):
        if not isinstance(file_list, list):
            file_list = [file_list]
        for file in file_list:
            mime: str = file['mime']
            mime_parts = mime.split("/")
            file['preview'] = {mime_parts[0]: file}  # specify preview as type:self

    #########

    # Displays the files in the file_page database as a list
    # This is primarily intended to be used to edit multiple file's tags at once
    # GET SUPPORT:
    #   Pagination ~ Page # Only => 'page'
    #       page counts from 1; to reflect the UI
    #########
    @classmethod
    def view_as_list(cls, request: Dict[str, Any]) -> ServeResponse:
        FIRST_PAGE = 0
        GET = request['GET']
        page = int(GET.get('page', 1)) - 1  # Assume page is [1,Infinity), map to [0,Infinity)
        PAGE_SIZE = 50
        PAGE_NEIGHBORS = 4

        search = GET.get("search", None)
        total_files = ApiPageGroup.get_file_count_internal(search=search)
        total_pages = PaginationUtil.get_page_count(PAGE_SIZE, total_files)
        # # Determine if page is valid
        # if not PaginationUtil.is_page_valid(page, page_size, file_count) and page != FIRST_PAGE:
        #     return StatusPageGroup.serve_error(404)

        file_list = ApiPageGroup.get_file_list_internal(page=page, size=PAGE_SIZE, search=search)

        # Get unique tags
        unique_tags = {}
        for file in file_list:
            for tag in file['tags']:
                if tag['id'] not in unique_tags:
                    unique_tags[tag['id']] = tag
        # Convert to list & Sort
        tag_list = [v for v in unique_tags.values()]
        tag_list.sort(key=lambda x: (-x['count'], x['name']))

        for file in file_list:
            file['tags'].sort(key=lambda x: x['name'])  # Sort tags by name

        serve_file = pathing.Static.get_html("file/list.html")
        result = serve(serve_file)

        def pagination_url_gen(id: int):
            return routing.FilePage.get_index_list(page=id + 1)

        context = {
            'page_title': "Files",
            'results': file_list,
            'tags': tag_list,
            'navbar': get_navbar_context(active=routing.FilePage.root),
            'subnavbar': {'list': 'active'},
            'pagination': PaginationUtil.get_pagination(page, total_pages, PAGE_NEIGHBORS, pagination_url_gen)
        }
        return reformat_serve(cls.renderer, result, context)

    #########
    # Displays the files in the file_page database as a list
    # This is primarily intended to be used to edit multiple file's tags at once
    # GET SUPPORT:
    #   Pagination ~ Page # Only => 'page'
    #       page counts from 1; to reflect the UI
    #########
    @classmethod
    def view_file(cls, request: Dict[str, Any]) -> ServeResponse:
        file = ApiPageGroup.get_file_internal(request['GET'].get('id'))

        file['tags'].sort(key=lambda x: (-x['count'], x['name']))

        cls.append_file_previews(file)
        cls.specify_edit_page(file)

        print(file)
        serve_file = pathing.Static.get_html("file/page.html")
        result = serve(serve_file)
        context = {
            'result': file,
            'tags': file['tags'],
            'navbar': get_navbar_context(),
            'subnavbar': {}
        }
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def handle_edit(cls, request: Dict[str, Any]) -> ServeResponse:
        method = request['REQUEST_METHOD']
        if method == "POST":
            return cls.view_file_edit_action(request)
        elif method == "GET":
            return cls.view_file_edit(request)
        else:
            return 405

    @classmethod
    def view_file_edit(cls, request: Dict[str, Any]) -> ServeResponse:
        file = ApiPageGroup.get_file_internal(request['GET'].get('id'))
        file['tags'].sort(key=lambda x: (x['name']))

        cls.append_file_previews(file)
        cls.specify_edit_page(file)
        serve_file = pathing.Static.get_html("file/page_edit.html")
        result = serve(serve_file)
        print(file)
        context = {
            'result': file,
            'tags': file['tags'],
            'navbar': get_navbar_context(),
            'subnavbar': {},
            'form': {
                'action': routing.FilePage.edit_file,
                'id': file['id']
            }
        }
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def view_file_edit_action(cls, request: Dict[str, Any]) -> ServeResponse:
        print(request)
        POST = request['POST']
        file_id = POST['id']
        tags: str = POST['tags']
        tag_list = tags.splitlines()
        tag_list = [tag.strip() for tag in tag_list]

        missing_tags = ApiPageGroup.get_valid_tags(tag_list, True)
        missing_tags_values = [(tag['name'], "") for tag in missing_tags]
        if len(missing_tags) > 0:
            ApiPageGroup.api.tag.insert(missing_tags_values)
        tag_ids: List[Union[str, int]] = [tag['id'] for tag in ApiPageGroup.get_valid_tags(tag_list)]

        update_args = {}

        def try_add(names: List[str], source: Dict, dest: Dict):
            for name in names:
                if name in source:
                    dest[name] = source[name]

        try_add(['name', 'description'], POST, update_args)
        update_args['tags'] = tag_ids

        ApiPageGroup.update_file_info_internal(file_id, **update_args)
        return StatusPageGroup.serve_submit_redirect(routing.FilePage.get_edit_file(id=file_id))

    @classmethod
    def serve_raw_file(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request.get('GET').get('id')
        client = dbapi.MasterClient(db_path=config.db_path)
        results = client.file.fetch(ids=[file_id])
        if len(results) == 0:
            return StatusPageGroup.serve_error(404)
        else:
            return serve(results[0]['path'], range=request.get("range", "bytes=0-"))

    @classmethod
    def serve_raw_page(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request.get('GET').get('id')
        client = dbapi.MasterClient(db_path=config.db_path)
        results = client.file.fetch(ids=[file_id])
        if len(results) == 0:
            return StatusPageGroup.serve_error(404)
        else:
            result = results[0]
            # print(result)
            mime = result['mime']
            # print(mime)
            # .split("/")[0]
            mime = mime.split("/")
            if len(mime) > 0:
                mime = mime[0]
            else:
                mime = ""

            raw_url = routing.FilePage.get_serve_file_raw(result['id'])
            if mime == "image":
                serve_file = pathing.Static.get_html("raw/image.html")
                ctx = {
                    "title": result['name'],
                    "source": raw_url
                }
                s = serve(serve_file)
                return reformat_serve(cls.renderer, s, ctx)
            else:
                return StatusPageGroup.serve_error(404)

    @classmethod
    def serve_slideshow(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request.get('GET').get('id')
        client = dbapi.MasterClient(db_path=config.db_path)
        results = client.file.fetch(ids=[file_id])
        if len(results) == 0:
            return StatusPageGroup.serve_error(404)
        else:
            result = results[0]
            mime = result['mime'].split("/")
            if len(mime) > 0:
                mime = mime[0]
            else:
                mime = ""

            raw_url = routing.FilePage.get_serve_file_raw(result['id'])
            serve_file = pathing.Static.get_html("file/ss.html")
            if mime == "image":
                ctx = {
                    "title": result['name'],
                    "image": {
                        "alt": result['description'],
                        "source": raw_url
                    }
                }
                s = serve(serve_file)
                return reformat_serve(cls.renderer, s, ctx)
            elif mime == "video":
                ctx = {
                    "title": result['name'],
                    "video": {
                        "alt": result['description'],
                        "source": raw_url,
                        "mime": result['mime']
                    }
                }
                s = serve(serve_file)
                return reformat_serve(cls.renderer, s, ctx)
            else:
                return StatusPageGroup.serve_error(404)

    @classmethod
    def specify_edit_page(cls, file):
        file['edit_page'] = routing.full_path(routing.FilePage.get_edit_file(file['id']))
