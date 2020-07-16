import os
from math import ceil
from typing import Dict, Tuple, Union, List, Set, Any
from litespeed import serve, route
from pystache import Renderer
from src.routing.pages import page_utils
import src.api.model_clients as clients
import src.api.models as models
from src.routing.pages.page_group import PageGroup
from src.routing.pages.tag_page_group import TagPageGroup
from src.routing.virtual_access_points import RequiredVap
from src.content.content_gen import ContentGeneration, GeneratedContentType
from src.util import dict_util, path_util
from src.routing.pages.page_utils import reformat_serve, escape_js_string

renderer = None
db_path = None


class FilePageGroup(PageGroup):
    renderer = None
    file_client = None
    file_search_client = None
    tag_client = None

    @classmethod
    def add_routes(cls):
        route(FilePageGroup.get_group_path(), function=cls.as_route_func(cls.index), no_end_slash=True, methods=['GET'])
        route(FilePageGroup.get_index(), function=cls.as_route_func(cls.index), no_end_slash=True, methods=['GET'])

        route(FilePageGroup.get_group_path('grid'), function=cls.as_route_func(cls.index_grid_paged), no_end_slash=True,
              methods=['GET'])
        route(FilePageGroup.get_group_path('list'), function=cls.as_route_func(cls.index_list_paged), no_end_slash=True,
              methods=['GET'])
        route(FilePageGroup.get_page("(\d*)"), function=cls.as_route_func(cls.file), methods=['GET'])
        route(FilePageGroup.get_page_edit("(\d*)"), function=cls.as_route_func(cls.file_edit), methods=['GET'])

        route(FilePageGroup.get_search(), function=cls.as_route_func(cls.search), no_end_slash=True, methods=['GET'])

        route(FilePageGroup.get_action_update_page("(\d*)"), function=cls.as_route_func(cls.action_update_page),
              no_end_slash=True, methods=['POST'])

    @classmethod
    def initialize(cls, **kwargs):
        db_path = dict_util.nested_get(kwargs, 'config.Launch Args.db_path')
        cls.file_client = clients.FilePage(db_path=db_path)
        cls.tag_client = clients.Tag(db_path=db_path)
        cls.file_search_client = clients.FilePageSearch(db_path=db_path)
        cls.renderer = Renderer(search_dirs=[RequiredVap.html_real("templates")])

    @classmethod
    def index(cls, request: Dict[str, Any]):
        return cls.index_paged(request)

    @classmethod
    def index_paged(cls, request: Dict[str, Any]):
        return cls.shared_index_paged(request, 'index_grid.html')

    @classmethod
    def index_grid_paged(cls, request: Dict[str, Any]):
        return cls.shared_index_paged(request, 'index_grid.html')

    @classmethod
    def index_list_paged(cls, request: Dict[str, Any]):
        return cls.shared_index_paged(request, 'index_list.html')

    @classmethod
    def shared_index_paged(cls, request: Dict[str, Any], html_name: str):
        GET = request.get('GET', {})
        page = GET.get('page', 1)
        display_page_number = int(page)
        count = GET.get('count', None)
        args = {}
        FilePageGroup.update_paged_args(display_page_number, page_size=count, args=args)
        pages = cls.file_client.get(**args)
        count = cls.file_client.count()

        if not FilePageGroup.is_valid_page(display_page_number, args.get('page_size'), count):
            if display_page_number != 1 and count != 0:
                return None, 404

        ctx = FilePageGroup.get_shared_index_data(pages, count, args, display_page_number, cls.get_index)
        ctx['navbar'] = cls.get_shared_navbar()

        file = RequiredVap.file_html_real(html_name)
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def get_shared_index_data(cls, pages, count, args, display_page_number, get_page_path):
        pagination_ctx = page_utils.get_pagination_symbols(count, args['page_size'], display_page_number, get_page_path)
        page_content = FilePageGroup.get_content(pages, GeneratedContentType.Thumbnail)
        page_ctx = FilePageGroup.reformat_page(page_content)
        sorted_unique_tags = FilePageGroup.sort_tags(FilePageGroup.get_unique_tags(pages))
        tag_ctx = FilePageGroup.reformat_tags(sorted_unique_tags, support_search=True)

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
        file = RequiredVap.file_html_real('index_grid.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def file(cls, request: Dict[str, Any], page_id: Union[str, int]):
        page_id = int(page_id)
        pages = cls.file_client.get(ids=[page_id])
        if pages is None or len(pages) < 0:
            return None, 404
        page = pages[0]
        ctx = {}
        _, content_virtual_path, content_real_path = cls.get_content(page, GeneratedContentType.Viewable)
        if content_real_path is not None and os.path.exists(content_real_path):
            v_ext = path_util.get_formatted_ext(content_virtual_path)
            content_type = page_utils.guess_content(v_ext)
            ctx['content'] = {}
            if content_type in ['video', 'audio']:
                remap_ext = {
                    'ogv': 'ogg'
                }
                r_ext = remap_ext.get(v_ext, v_ext)
                ctx['content'][content_type] = {
                    'sources': {
                        'path': content_virtual_path,
                        'type': r_ext
                    }
                }
            else:
                ctx['content'][content_type] = {
                    'content_path': content_virtual_path
                }
        ctx.update(page.to_dictionary())
        if page.name is not None:
            ctx['page_title'] = page.name
        else:
            del ctx['name']
        if page.description is not None:
            ctx['description'] = page.description
        else:
            del ctx['description']

        ctx['file']['extension'] = ctx['file']['extension'].upper()
        ctx['file']['name'] = os.path.basename(ctx['file']['path'])
        ctx['tags'] = cls.reformat_tags(page.tags)
        ctx['navbar'] = cls.get_shared_navbar()
        ctx['edit_path'] = cls.get_page_edit(page_id)
        file = RequiredVap.file_html_real('page.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def file_edit(cls, request: Dict[str, Any], page_id: Union[str, int]):
        page_id = int(page_id)
        pages = cls.file_client.get(ids=[page_id])
        if pages is None or len(pages) < 0:
            return None, 404
        page = pages[0]
        ctx = {}
        _, content_virtual_path, content_real_path = cls.get_content(page, GeneratedContentType.Viewable)
        if content_real_path is not None and os.path.exists(content_real_path):
            v_ext = path_util.get_formatted_ext(content_virtual_path)
            content_type = page_utils.guess_content(v_ext)
            ctx['content'] = {}
            if content_type in ['video', 'audio']:
                remap_ext = {
                    'ogv': 'ogg'
                }
                r_ext = remap_ext.get(v_ext, v_ext)
                ctx['content'][content_type] = {
                    'sources': {
                        'path': content_virtual_path,
                        'type': r_ext
                    }
                }
            else:
                ctx['content'][content_type] = {
                    'content_path': content_virtual_path
                }
        ctx.update(page.to_dictionary())
        if page.name is not None:
            ctx['page_title'] = page.name
        ctx['file']['extension'] = ctx['file']['extension'].upper()
        ctx['file']['name'] = os.path.basename(ctx['file']['path'])
        ctx['tags'] = cls.reformat_tags(page.tags)
        ctx['navbar'] = cls.get_shared_navbar()
        ctx['show_path'] = cls.get_page(page_id)
        ctx['actions'] = {'edit_filepage': {'path': cls.get_action_update_page(page_id)}}
        file = RequiredVap.file_html_real('edit.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def action_update_page(cls, request: Dict[str, Any], page_id: Union[str, int]):
        page_id = int(page_id)

        # FIX NAME?/DESC
        name = request['POST'].get('title')
        description = request['POST'].get('description')
        cls.file_client.set_page_values(page_id, name, description)

        # FIX TAGS
        tags = request['POST'].get('tags', '').splitlines()
        for i in range(0, len(tags)):
            tags[i] = tags[i].strip()
        cls.tag_client.add_missing_tags(tags)
        cls.file_client.set_tags(page_id, tags)

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
    def get_unique_tags(pages: Union[models.Page, List[models.Page]]) -> List[models.Tag]:
        def parse(page: models.Page) -> Set[models.Tag]:
            return set(page.tags)

        if not isinstance(pages, List):
            return list(parse(pages))

        output_rows = set()
        for page in pages:
            output_rows.update(parse(page))
        return list(output_rows)

    @staticmethod
    def sort_tags(tags: List[models.Tag], desc: bool = True) -> List[models.Tag]:
        def get_key(tag: models.Tag) -> Any:
            if desc:
                return (-tag.count, tag.name)
            else:
                return (tag.count, tag.name)

        tags.sort(key=get_key)
        return tags

    @staticmethod
    def reformat_page(
            pages: Union[Tuple[models.Page, str, str], List[Tuple[models.Page, str, str]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:

        def parse(page_content_pair: Tuple[models.Page, str, str]) -> Dict[str, Any]:
            page, content_virtual_path, content_real_path = page_content_pair
            d = page.to_dictionary()
            d['page_path'] = FilePageGroup.get_page(page.page_id)
            ext = d['file']['extension']
            d['file']['extension'] = ext.upper()

            if content_real_path is not None and os.path.exists(content_real_path):
                v_ext = path_util.get_formatted_ext(content_virtual_path)
                content_type = page_utils.guess_content(v_ext)
                d['content'] = {}
                d['content'][content_type] = {
                    'content_path': content_virtual_path
                }
            return d

        if not isinstance(pages, List):
            return parse(pages)

        output_rows = []
        for page in pages:
            output_rows.append(parse(page))
        return output_rows

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

    @staticmethod
    def get_content(
            file_pages: Union[models.FilePage, List[models.FilePage]],
            content_type: GeneratedContentType
    ) -> Union[Tuple[models.FilePage, str, str], List[Tuple[models.FilePage, str, str]]]:

        def parse(file_page: models.FilePage) -> Tuple[models.FilePage, Any, Any]:
            ext = file_page.file.extension.lower()
            resource_path = ContentGeneration.get_file_name(content_type, ext)
            partial_path = f"file/{file_page.file.file_id}/{resource_path}"
            virtual_path = RequiredVap.dynamic_generated_virtual(partial_path)
            real_path = RequiredVap.dynamic_generated_real(partial_path)
            if content_type is None or not os.path.exists(real_path):
                return file_page, None, None
            else:
                return file_page, virtual_path, real_path

        if not isinstance(file_pages, List):
            return parse(file_pages)

        output_rows = []
        for img in file_pages:
            output_rows.append(parse(img))
        return output_rows

    @staticmethod
    def reformat_tags(
            tags: Union[models.Tag, List[models.Tag]], support_search: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        SEARCH_FORM_ID = 'tagsearchbox'

        def parse(tag: models.Tag) -> Dict[str, Any]:
            tag_d = tag.to_dictionary()
            tag_d['page_path'] = TagPageGroup.get_page(tag.id)
            if support_search:
                tag_d['search_support'] = {
                    'search_id': SEARCH_FORM_ID,
                    'js_name': escape_js_string(tag.name.replace(' ', '_'))
                }
            return tag_d

        if not isinstance(tags, List):
            return parse(tags)

        output_rows = []
        for tag in tags:
            output_rows.append(parse(tag))
        return output_rows
