import os
from math import ceil
from typing import Dict, Tuple, Union, List, Set, Any

from litespeed import serve, route
from pystache import Renderer
from src.Routing.Pages import page_utils
import src.API.model_clients as Clients
import src.API.models as Models
from src.Routing.Pages.page_group import PageGroup
from src.Routing.virtual_access_points import RequiredVap, VirtualAccessPoints as VAP
from src import DatabaseSearch
from src.content.content_gen import ContentGeneration, GeneratedContentType
from src.util.db_util import Conwrapper, convert_tuple_to_list
from src.util import dict_util
# define renderer
from src.Routing.Pages.errors import serve_error
from src.Routing.Pages.page_utils import reformat_serve, escape_js_string

renderer = None
db_path = None


class TagPageGroup(PageGroup):
    @classmethod
    def get_page(cls, id: str):
        return "/"


class FilePageGroup(PageGroup):
    renderer = None
    file_client = None
    file_search_client = None
    tag_client = None

    @classmethod
    def add_routes(cls):
        route(FilePageGroup.get_index(), f=cls.as_route_func(cls.index), methods=['GET'])
        route(FilePageGroup.get_index("(\d*)"), f=cls.as_route_func(cls.index_paged), methods=['GET'])

        route(FilePageGroup.get_page("(\d*)"), f=cls.as_route_func(cls.file), methods=['GET'])
        route(FilePageGroup.get_page_edit("(\d*)"), f=cls.as_route_func(cls.file_edit), methods=['GET'])

        route(FilePageGroup.get_search(), f=cls.as_route_func(cls.search), no_end_slash=True, methods=['GET'])
        route(FilePageGroup.get_search("(\d*)"), f=cls.as_route_func(cls.search_paged), no_end_slash=True,
              methods=['GET'])

    @classmethod
    def initialize(cls, **kwargs):
        db_path = dict_util.nested_get(kwargs, 'config.Launch Args.db_path')
        cls.file_client = Clients.FilePage(db_path=db_path)
        cls.tag_client = Clients.Tag(db_path=db_path)
        cls.file_search_client = Clients.FilePageSearch(db_path=db_path)
        cls.renderer = Renderer(search_dirs=[RequiredVap.html_real("templates")])

    @classmethod
    def index(cls, request: Dict[str, Any]):
        return cls.index_paged(request, 1)

    @classmethod
    def index_paged(cls, request: Dict[str, Any], display_page_number: Union[str, int]):
        display_page_number = int(display_page_number)
        args = {}
        FilePageGroup.update_paged_args(display_page_number, args=args)
        pages = cls.file_client.get(**args)
        count = cls.file_client.count()

        if not FilePageGroup.is_valid_page(display_page_number, args.get('page_size'), count):
            return None, 404
        ctx = FilePageGroup.get_shared_index_data(pages, count, args, display_page_number, cls.get_index)

        file = RequiredVap.file_html_real('index.html')
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
        return cls.search_paged(request, 1)

    @classmethod
    def search_paged(cls, request: Dict[str, Any], display_page_number: Union[str, int]):
        display_page_number = int(display_page_number)
        search = request.get('GET', {}).get('search', None)
        if search is None:
            return cls.index_paged(request, display_page_number)
        search = search.strip()
        if len(search) == 0:
            return cls.index_paged(request, display_page_number)

        args = {'search': search}
        FilePageGroup.update_paged_args(display_page_number, args=args)
        pages, count = cls.file_search_client.get_and_count(**args)

        if not FilePageGroup.is_valid_page(display_page_number, args.get('page_size'), count):
            return None, 404

        def get_page_path(page: int):
            return cls.get_search(page, search)

        ctx = FilePageGroup.get_shared_index_data(pages, count, args, display_page_number, get_page_path)
        ctx['search'] = search

        file = RequiredVap.file_html_real('index.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def file(cls, request: Dict[str, Any], page_id: Union[str, int]):
        page_id = int(page_id)
        pages = cls.file_client.get(ids=[page_id])
        if pages is None or len(pages) < 0:
            return None, 404
        page = pages[0]

        ctx = {
            'page_title': page.name,
        }
        ctx.update(page.to_dictionary)
        ctx['tags'] = page.reformat_tags(page.tags)

        file = RequiredVap.file_html_real('page.html')
        result = serve(file)
        return reformat_serve(cls.renderer, result, ctx)

    @classmethod
    def file_edit(cls, request: Dict[str, Any], page_id: Union[str, int]):
        return None, 404

    @classmethod
    def get_page(cls, page_id: Union[str, int]):
        return f"/show/file/{page_id}"

    @classmethod
    def get_page_edit(cls, page_id: Union[str, int]):
        return f"/show/file/{page_id}/edit"

    @classmethod
    def get_index(cls, page_id: Union[str, int] = None):
        if page_id is None:
            return f"/show/file/index"
        else:
            return f"/show/file/index/{page_id}"

    @classmethod
    def get_search(cls, page_id: Union[str, int] = None, search: str = None):
        if page_id is None:
            path = f"/show/file/search"
        else:
            path = f"/show/file/search/{page_id}"
        if search is not None:
            path += f"?search={search}"
        return path

    @staticmethod
    def update_paged_args(page: int, page_size: int = 50, args: Dict = None, is_page_real: bool = True):
        if args is None:
            args = {}
        if is_page_real:
            usable_page = page - 1
        else:
            usable_page = page

        args['offset'] = usable_page * page_size
        args['page_size'] = page_size

    @staticmethod
    def is_valid_page(display_page, page_size, total_items) -> bool:
        min_page = 1
        max_page = ceil(total_items / page_size)
        return min_page <= display_page <= max_page

    @staticmethod
    def get_unique_tags(pages: Union[Models.Page, List[Models.Page]]) -> List[Models.Tag]:
        def parse(page: Models.Page) -> Set[Models.Tag]:
            return set(page.tags)

        if not isinstance(pages, List):
            return list(parse(pages))

        output_rows = set()
        for page in pages:
            output_rows.update(parse(page))
        return list(output_rows)

    @staticmethod
    def sort_tags(tags: List[Models.Tag], desc: bool = True) -> List[Models.Tag]:
        def get_key(tag: Models.Tag) -> Any:
            if desc:
                return (-tag.count, tag.name)
            else:
                return (tag.count, tag.name)

        tags.sort(key=get_key)
        return tags

    @staticmethod
    def reformat_page(
            pages: Union[Tuple[Models.Page, str], List[Tuple[Models.Page, str]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:

        def parse(page_content_pair: Tuple[Models.Page, str]) -> Dict[str, Any]:
            page, content = page_content_pair
            d = page.to_dictionary()
            d['page_path'] = TagPageGroup.get_page(page.page_id)
            ext = d['file']['extension']
            d['file']['extension'] = ext.upper()
            return d

        if not isinstance(pages, List):
            return parse(pages)

        output_rows = []
        for page in pages:
            output_rows.append(parse(page))
        return output_rows

    @staticmethod
    def get_content(
            file_pages: Union[Models.FilePage, List[Models.FilePage]],
            content_type: GeneratedContentType
    ) -> Union[Tuple[Models.FilePage, str], List[Tuple[Models.FilePage, str]]]:

        def parse(file_page: Models.FilePage) -> Tuple[Models.FilePage, Any]:
            ext = file_page.file.extension.lower()
            resource_path = ContentGeneration.get_file_name(content_type, ext)
            partial_path = f"file/{file_page.file.file_id}/{resource_path}"
            virtual_path = RequiredVap.dynamic_generated_virtual(partial_path)
            real_path = RequiredVap.dynamic_generated_real(partial_path)
            if content_type is None or not os.path.exists(real_path):
                return file_page, None
            else:
                return file_page, virtual_path

        if not isinstance(file_pages, List):
            return parse(file_pages)

        output_rows = []
        for img in file_pages:
            output_rows.append(parse(img))
        return output_rows

    @staticmethod
    def reformat_tags(
            tags: Union[Models.Tag, List[Models.Tag]], support_search: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        SEARCH_FORM_ID = 'tagsearchbox'

        def parse(tag: Models.Tag) -> Dict[str, Any]:
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
