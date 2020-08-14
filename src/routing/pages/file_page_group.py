import mimetypes
import os
from functools import partial
from math import ceil
from typing import Dict, Tuple, Union, List, Set, Any
from litespeed import serve, route
from pystache import Renderer

from src.content.management.content_management import ContentManager, ContentGenerator
from src.routing.content_gen_group import GeneratedContentGroup
from src.routing.pages import page_utils
from src.routing.pages.page_group import PageGroup
from src.routing.pages.tag_page_group import TagPageGroup
from src.routing.virtual_access_points import RequiredVap
from src.content.gen.content_gen import StaticContentType
from src.util import dict_util, path_util
from src.routing.pages.page_utils import reformat_serve, escape_js_string
from src.database.clients import PageClient, TagClient, MasterClient


class FilePageGroup(PageGroup):
    renderer = None
    file_search_client = None

    client = None  # MasterClient()
    content_manager = None  # ContentManager()

    @classmethod
    def add_routes(cls):
        route(FilePageGroup.get_group_path(),
              function=cls.as_route_func(cls.index),
              no_end_slash=True,
              methods=['GET'])
        route(FilePageGroup.get_index(),
              function=cls.as_route_func(cls.index),
              no_end_slash=True,
              methods=['GET'])
        route(FilePageGroup.get_page("(\d*)"),
              function=cls.as_route_func(cls.file),
              methods=['GET'])
        route(FilePageGroup.get_page_edit("(\d*)"),
              function=cls.as_route_func(cls.file_edit),
              methods=['GET'])
        route(FilePageGroup.get_search(),
              function=cls.as_route_func(cls.search),
              no_end_slash=True,
              methods=['GET'])
        route(FilePageGroup.get_action_update_page("(\d*)"),
              function=cls.as_route_func(cls.action_update_page),
              no_end_slash=True,
              methods=['POST'])

    @classmethod
    def initialize(cls, **kwargs):
        db_path = dict_util.nested_get(kwargs, 'config.Launch Args.db_path')
        cls.client = MasterClient(db_path=db_path)
        cls.content_manager = kwargs.get('content_manager')  # ContentManager(ContentGenerator())
        cls.renderer = Renderer(search_dirs=[RequiredVap.html_real("templates")])

    @classmethod
    def index(cls, request: Dict[str, Any]):
        return cls.index_paged(request)

    @classmethod
    def index_paged(cls, request: Dict[str, Any]):
        GET = request.get('GET', {})
        page = GET.get('page', 1)
        display_page_number = int(page)
        count = GET.get('count', None)
        args = {}
        FilePageGroup.update_paged_args(display_page_number, page_size=count, args=args)
        pages = cls.get_file_page_info(**args)
        count = cls.file_client.count()

        if not FilePageGroup.is_valid_page(display_page_number, args.get('page_size'), count):
            return None, 404
        ctx = FilePageGroup.get_shared_index_data(pages, count, args, display_page_number, cls.get_index)
        ctx['navbar'] = cls.get_shared_navbar()

        file = RequiredVap.file_html_real('index.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def get_shared_index_data(cls, pages, count, args, display_page_number, get_page_path):
        pagination_ctx = page_utils.get_pagination_symbols(count, args['page_size'], display_page_number, get_page_path)
        page_content = cls.get_content(pages, GeneratedContentType.Thumbnail)
        page_ctx = cls.reformat_page(page_content)
        sorted_unique_tags = cls.sort_tags(FilePageGroup.get_unique_tags(pages))
        tag_ctx = cls.reformat_tags(sorted_unique_tags, support_search=True)

        return {
            'page_title': "File Index",
            'pages': page_ctx,
            'tags': tag_ctx,
            'pagination': pagination_ctx
        }

    @classmethod
    def search(cls, request: Dict[str, Any]):
        return cls.search_paged(request)

    @classmethod
    def search_paged(cls, request: Dict[str, Any]):
        GET = request.get('GET', {})
        search = GET.get('search', None)
        page = GET.get('page', 1)
        display_page_number = int(page)
        count = GET.get('count', None)
        if search is None:
            return cls.index_paged(request)
        search = search.strip()
        if len(search) == 0:
            return cls.index_paged(request)

        args = {'search': search}
        FilePageGroup.update_paged_args(display_page_number, page_size=count, args=args)
        pages, count = cls.file_search_client.get_and_count(**args)

        if not FilePageGroup.is_valid_page(display_page_number, args.get('page_size'), count):
            return None, 404

        def get_page_path(page: int):
            return cls.get_search(page, search, page=page, count=count)

        ctx = FilePageGroup.get_shared_index_data(pages, count, args, display_page_number, get_page_path)
        ctx['search'] = search

        ctx['navbar'] = cls.get_shared_navbar()
        file = RequiredVap.file_html_real('index.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def file(cls, request: Dict[str, Any], file_id: Union[str, int]):
        file_id = int(file_id)
        file_pages = cls.client.file_page_info.fetch(file_ids=[file_id])
        if file_pages is None or len(file_pages) < 0:
            return None, 404
        file_page = file_pages[0]
        cls.reformat_page_info(file_page, StaticContentType.Viewable)
        tags = cls.get_file_tag_info(file_ids=[file_id])
        tags = cls.sort_tags(tags)
        cls.reformat_tags(tags)
        context = {}

        context['page'] = file_page
        context['tags'] = tags
        context['navbar'] = cls.get_shared_navbar()

        file = RequiredVap.file_html_real('page.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def file_edit(cls, request: Dict[str, Any], page_id: Union[str, int]):
        # page_id = int(page_id)
        # pages = cls.file_client.get(ids=[page_id])
        # if pages is None or len(pages) < 0:
        #     return None, 404
        # page = pages[0]
        # ctx = {}
        # _, content_virtual_path, content_real_path = cls.get_content(page, GeneratedContentType.Viewable)
        # if content_real_path is not None and os.path.exists(content_real_path):
        #     v_ext = path_util.get_formatted_ext(content_virtual_path)
        #     content_type = page_utils.guess_content(v_ext)
        #     ctx['content'] = {}
        #     if content_type in ['video', 'audio']:
        #         remap_ext = {
        #             'ogv': 'ogg'
        #         }
        #         r_ext = remap_ext.get(v_ext, v_ext)
        #         ctx['content'][content_type] = {
        #             'sources': {
        #                 'path': content_virtual_path,
        #                 'type': r_ext
        #             }
        #         }
        #     else:
        #         ctx['content'][content_type] = {
        #             'content_path': content_virtual_path
        #         }
        # ctx.update(page.to_dictionary())
        # if page.name is not None:
        #     ctx['page_title'] = page.name
        # ctx['file']['extension'] = ctx['file']['extension'].upper()
        # ctx['file']['name'] = os.path.basename(ctx['file']['path'])
        # ctx['tags'] = cls.reformat_tags(page.tags)
        # ctx['navbar'] = cls.get_shared_navbar()
        # ctx['show_path'] = cls.get_page(page_id)
        # ctx['actions'] = {'edit_filepage': {'path': cls.get_action_update_page(page_id)}}
        # file = RequiredVap.file_html_real('edit.html')
        # result = serve(file)
        # return reformat_serve(cls.renderer, result, ctx)
        return 404

    @classmethod
    def action_update_page(cls, request: Dict[str, Any], page_id: Union[str, int]):
        page_id = int(page_id)

        # FIX NAME?/DESC
        name = request['POST'].get('title')
        description = request['POST'].get('description')
        # cls.file_client.set_page_values(page_id, name, description)

        # FIX TAGS
        tags = request['POST'].get('tags', '').splitlines()
        for i in range(0, len(tags)):
            tags[i] = tags[i].strip()
        # cls.tag_client.add_missing_tags(tags)
        # cls.file_client.set_tags(page_id, tags)

        file = RequiredVap.html_real('redirect.html')
        ctx = {
            'redirect': cls.get_page_edit(page_id)
        }
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def get_group_path(cls, path: str = None):
        result = f"/show/file"
        if path is not None:
            if path[0] != '/':
                result += '/'
            result += str(path)
        return result

    @classmethod
    def get_page(cls, page_id: Union[str, int]):
        return cls.get_group_path(str(page_id))

    @classmethod
    def get_page_edit(cls, page_id: Union[str, int]):
        return cls.get_group_path(f"{page_id}/edit")

    @classmethod
    def get_index(cls, page_id: Union[str, int] = None, **kwargs):
        path = cls.get_group_path("index")
        if page_id is not None:
            kwargs['page'] = page_id
        path += PageGroup.to_get_string(**kwargs)
        return path

    @classmethod
    def get_search(cls, page_id: Union[str, int] = None, search: str = None, **kwargs):
        path = cls.get_group_path("search")
        if page_id is not None:
            kwargs['page'] = page_id
        if search is not None:
            kwargs['search'] = search
        path += PageGroup.to_get_string(**kwargs)
        return path

    @classmethod
    def get_action_update_page(cls, page_id: Union[str, int]):
        return f"/actions/update/file_page/{page_id}"

    @staticmethod
    def update_paged_args(page: int, page_size: int = 50, args: Dict = None, is_page_real: bool = True):
        if args is None:
            args = {}
        if is_page_real:
            usable_page = page - 1
        else:
            usable_page = page
        if page_size is None:
            page_size = 50

        args['offset'] = usable_page * page_size
        args['page_size'] = page_size

    @staticmethod
    def is_valid_page(display_page, page_size, total_items) -> bool:
        min_page = 1
        max_page = ceil(total_items / page_size)
        return min_page <= display_page <= max_page

    @staticmethod
    def sort_tags(tags: List[Dict[str, Any]], desc: bool = True) -> List[Dict[str, Any]]:
        def get_key(tag: Dict[str, Any]) -> Any:
            if desc:
                return (-tag['count'], tag['name'])
            else:
                return (tag['count'], tag['name'])

        tags.sort(key=get_key)
        return tags

    @classmethod
    def get_shared_navbar(cls):
        def create_nav(name, path, is_current=False, is_disabled=False):
            nav_ctx = {
                'text': name,
                'path': path,
            }
            if is_current:
                nav_ctx['status'] = 'active'
            elif is_disabled:
                nav_ctx['status'] = 'disable'
            return nav_ctx

        navs = [
            create_nav('Home', '/'),
            create_nav('Files', cls.get_index(), is_current=True)
        ]
        return navs

    @classmethod
    def get_file_page_info(cls, **kwargs) -> List[Dict[str, Any]]:
        return cls.client.file_page_info.fetch(**kwargs)

    @classmethod
    def get_file_tag_info(cls, **kwargs) -> List[Dict[str, Any]]:
        lookup = cls.client.file_tag_info.fetch_lookup(key='tag_id', **kwargs)
        unique = lookup.values()
        for item in unique:
            del item['file_id']
        return unique

    @classmethod
    def get_file_content_context(cls, file_id: int, content_type: StaticContentType) -> Dict[str, Any]:
        return GeneratedContentGroup.get_file_content_context(file_id, content_type)

    @classmethod
    def set_page_content(cls, page: Dict[str, Any], content_type: StaticContentType):
        page['content'] = cls.get_file_content_context(page['id'], content_type)

    @classmethod
    def set_page_path(cls, page: Dict[str, Any]):
        page['page_url'] = cls.get_page(page['id'])

    @classmethod
    def set_page_edit_path(cls, page: Dict[str, Any]):
        page['page_edit_url'] = cls.get_page_edit(page['id'])

    @classmethod
    def reformat_page_info(cls, pages: Dict[str, Any], content_type: StaticContentType):
        functions = [
            partial(cls.set_page_content, content_type=content_type),
            cls.set_page_path,
            cls.set_page_edit_path
        ]
        cls.apply_modifiers(pages, functions)

    @classmethod
    def apply_modifiers(cls, pages: Union[Dict[str, Any], List[Dict[str, Any]]], *functions):

        def fix_page(page: Dict[str, Any]):
            for function in functions:
                function(page)

        if not isinstance(pages, List):
            return fix_page(pages)

        for i in range(len(pages)):
            fix_page(pages[i])

    @staticmethod
    def reformat_tags(tags: Union[Dict[str, Any], List[Dict[str, Any]]], support_search: bool = False):
        SEARCH_FORM_ID = 'tagsearchbox'

        def fix_tag(tag: Dict[str, Any]):
            tag['page_path'] = TagPageGroup.get_page(tag['id'])
            if support_search:
                escaped_name = tag['name']
                tag['search_support'] = {
                    'search_id': SEARCH_FORM_ID,
                    'js_name': escape_js_string(escaped_name.replace(' ', '_'))
                }

        if not isinstance(tags, List):
            return fix_tag(tags)

        for i in range(len(tags)):
            fix_tag(tags[i])
