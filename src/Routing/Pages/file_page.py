import os
from math import ceil
from typing import Dict, Tuple, Union, List, Set, Any

from litespeed import serve, route
from pystache import Renderer
from src.Routing.Pages import page_utils
import src.API.model_clients as Clients
import src.API.models as Models
from src.Routing.virtual_access_points import RequiredVap, VirtualAccessPoints as VAP
from src import DatabaseSearch
from src.content.content_gen import ContentGeneration, GeneratedContentType
from src.util.db_util import Conwrapper, convert_tuple_to_list

# define renderer
from src.Routing.Pages.errors import serve_error
from src.Routing.Pages.page_utils import reformat_serve

renderer = None
db_path = None


def initialize_module(**kwargs):
    global renderer
    global db_path
    config = kwargs.get('config', {})
    launch_args = config.get('Launch Args', {})
    search_dirs = launch_args.get('template_dirs', [RequiredVap.html_real("templates")])
    renderer = Renderer(search_dirs=search_dirs)
    db_path = launch_args.get('db_path', RequiredVap.data_real('mediaserver.db'))


# hardcoded for now
def add_routes():
    route(r"show/file/index", f=show_file_index, methods=['GET'])
    route(r"show/file/index/(\d*)", f=show_file_index_paged, methods=['GET'])
    route(r"show/file/(\d*)", f=show_file, methods=['GET'])
    route(r"show/file/(\d*)/edit", f=show_file_edit, methods=['GET'])
    route(r"show/file/search", f=show_file_list_search, no_end_slash=True, methods=['GET'])
    route(r"show/file/search/(\d*)", f=show_file_list_paged_search, no_end_slash=True, methods=['GET'])


def escape_js_string(input: str) -> str:
    input = input.replace('/', '//')
    input = input.replace("'", '/')
    input = input.replace('"', '/"')
    return input


def get_paged_contexts(client: Clients.FilePage, **kwargs) -> Tuple[
    Union[None, int], Union[None, Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]]]:
    real_page = int(kwargs.get('page', 1)) - 1
    display_page = real_page + 1
    page_size = int(kwargs.get('page_size', 50))
    offset = page_size * real_page
    if real_page < 0:
        return 404, None

    if 'search' in kwargs:
        items = kwargs['search'].split()
        for i in range(len(items)):
            items[i] = items[i].replace('_', ' ')
        search_groups = DatabaseSearch.create_simple_search_groups(items)
        query = DatabaseSearch.create_query_from_search_groups(search_groups)
        with Conwrapper(db_path=client.db_path) as (conn, cursor):
            cursor.execute(query)
            results = cursor.fetchall()
        all_ids = convert_tuple_to_list(results)
        count = len(all_ids)
        ids = all_ids[offset:offset + page_size]
        requested = client.get(ids=ids)

    else:
        req_kwargs = dict(kwargs)
        req_kwargs['offset'] = offset
        req_kwargs['page_size'] = page_size
        count_kwargs = dict(kwargs)
        del count_kwargs['page_size']

        requested = client.get(**req_kwargs)
        count = client.count(**count_kwargs)

    if real_page > ceil(count / page_size) - 1:
        return 404, None

    get_paged_path = kwargs.get('get_paged_path')
    page_context = page_utils.get_pagination_symbols(count, page_size, display_page, get_paged_path)
    img_context = parse_rest_file(requested, GeneratedContentType.Thumbnail)
    tags = get_unique_tags(requested)
    tags = tag_sort_by_count(tags)
    tag_context = parse_rest_tags(tags, support_search=kwargs.get('support_search', False))
    return None, (img_context, tag_context, page_context)


def show_file_index(request):
    return show_file_index_paged(request, 1)


def show_file_index_paged(request, page: int):
    def get_paged_path(local_page: int) -> str:
        return f"show/file/index/{local_page}"

    desired_file = RequiredVap.file_html_real("index.html")
    file_client = Clients.FilePage(db_path=db_path)
    error, result = get_paged_contexts(file_client, page=page, page_size=75, get_paged_path=get_paged_path,
                                       support_search=True)
    if error is not None:
        return serve_error(error)
    file, tag, page = result

    context = {
        'TITLE': "Title",
        'FILES': file,
        'TAG_LIST': tag,
    }
    context.update(page)
    return reformat_serve(renderer, serve(desired_file), context)


# @route("show/file/search/([\w%'\s]*)", no_end_slash=True)
def show_file_list_search(request):
    return show_file_list_paged_search(request, 1)


# @route(f"show/file/search/(\d*)/([\w%'\s]*)", no_end_slash=True)
def show_file_list_paged_search(request, page: int):
    def get_paged_path(local_page: int) -> str:
        return f"show/file/search/{local_page}"

    desired_file = RequiredVap.file_html_real("index.html")
    file_client = Clients.FilePage(db_path=db_path)
    search = request.get('GET', {}).get('search', None)
    error, result = get_paged_contexts(file_client, page=page, page_size=75, get_paged_path=get_paged_path,
                                       search=search, support_search=True)
    if error is not None:
        return serve_error(error)
    file, tag, page = result

    context = {
        'TITLE': "Title",
        'FILES': file,
        'TAG_LIST': tag,
        'SEARCH': search,
    }
    context.update(page)
    return reformat_serve(renderer, serve(desired_file), context)


def show_file_shared(request, img_id) -> Union[
    Tuple[bool, int], Tuple[bool, Tuple[Dict[str, Any], Dict[str, Any], Models.FilePage]]]:
    file_client = Clients.FilePage(db_path=db_path)
    req_imgs = file_client.get(ids=[img_id])
    if req_imgs is None or len(req_imgs) < 1:
        return False, 404
    req_imgs = req_imgs[0]
    img_context = parse_rest_file(req_imgs, GeneratedContentType.Viewable)
    tag_context = parse_rest_tags(req_imgs.tags, support_search=False)
    return True, (img_context, tag_context, req_imgs)


def show_file(request, img_id):
    success, result = show_file_shared(request, img_id)
    if not success:
        return serve_error(result)
    img_context, tag_context, file = result

    desired_file = RequiredVap.file_html_real("page.html")
    context = {
        'TITLE': file.name,
        'TAG_LIST': tag_context
    }
    context.update(img_context)
    return reformat_serve(renderer, serve(desired_file), context)


def show_file_edit(request, img_id):
    success, result = show_file_shared(request, img_id)
    if not success:
        return serve_error(result)
    img_context, tag_context, file = result

    desired_file = RequiredVap.file_html_real("edit.html")
    context = {
        'TITLE': file.name,
        'TAG_LIST': tag_context
    }
    context.update(img_context)
    return reformat_serve(renderer, serve(desired_file), context)


CONTENT_IMAGE = 'Image'
CONTENT_DOCUMENT = 'Document'


def guess_content(ext: str) -> Union[None, str]:
    image_ext = ['png', 'jpeg', 'gif', 'jpg', 'psd', 'tif', 'tiff', 'svg']
    doc_ext = ['pdf', 'ai', ]
    if ext in image_ext:
        return CONTENT_IMAGE
    elif ext in doc_ext:
        return CONTENT_DOCUMENT
    else:
        return None


def parse_rest_file(file_pages: Union[Models.FilePage, List[Models.FilePage]], content_path: GeneratedContentType) -> Union[
    Dict[str, object], List[Dict[str, object]]]:
    def parse(file_page: Models.FilePage):
        base = {
            'page_path': f"show/file/{file_page.file_page_id}",
            'PAGE_ID': file_page.page_id,
            'FILE_PAGE_ID': file_page.file_page_id
        }
        if file_page.name is not None:
            base['page_name'] = str(file_page.name)
        else:
            base['page_name'] = 'Untitled'

        alt = ''
        if file_page.description is not None:
            alt = str(file_page.description)
            base['PAGE_DESCRIPTION'] = alt

        unsupported = False
        ext = file_page.file.extension.lower()
        type = guess_content(ext)
        resource_path = ContentGeneration.get_file_name(content_path, ext)
        partial_path = f"file/{file_page.file.file_id}/{resource_path}"
        virtual_path = RequiredVap.dynamic_generated_virtual(partial_path)
        real_path = RequiredVap.dynamic_generated_real(partial_path)
        if type is None or content_path is None or not os.path.exists(real_path):
            unsupported = True
            err_msg = f"{file_page.page_id} ~ {ext}:\n"
            if type is None:
                err_msg += f"\tGuessed None Type!\n"
            if content_path is None:
                err_msg += f"\tNo Content!\n"
            if not os.path.exists(real_path):
                err_msg += f"\tMissing Content!\n"
            print(err_msg)


        elif type == CONTENT_IMAGE:
            base['image'] = \
                {
                    'source_path': virtual_path,
                    'alternate_text': f'{alt}'
                }
        elif type == CONTENT_DOCUMENT:
            base['document'] = \
                {
                    'source_path': virtual_path,
                    'alternate_text': f'{alt}'
                }
        else:
            unsupported = True

        if unsupported:
            base['unsupported'] = \
                {
                    'extension': file_page.file.extension.upper(),
                    'alternate_text': f'{alt}'
                }
        return base

    if not isinstance(file_pages, List):
        return parse(file_pages)

    output_rows = []
    for img in file_pages:
        output_rows.append(parse(img))
    return output_rows


def get_unique_tags(imgs: Union[Models.Page, List[Models.Page]]) -> List[Models.Tag]:
    def parse(input_img: Models.Page) -> Set[Models.Tag]:
        unique_tags = set(input_img.tags)
        return unique_tags

    if not isinstance(imgs, List):
        return list(parse(imgs))

    output_rows = set()
    for img in imgs:
        output_rows.update(parse(img))
    return list(output_rows)


def tag_sort_by_count(tags: List[Models.Tag], desc: bool = True) -> List[Models.Tag]:
    def get_count(tag: Models.Tag) -> int:
        return tag.count

    tags.sort(key=get_count, reverse=desc)
    return tags


def parse_rest_tags(tags: Union[Models.Tag, List[Models.Tag]], support_search: bool = False) -> Union[
    Dict[str, object], List[Dict[str, object]]]:
    def parse(input_tag: Models.Tag):
        result = {
            'PAGE_PATH': f"/show/tag/{input_tag.id}",
            'TAG_ID': input_tag.id,
            'TAG_NAME': input_tag.name,
            'TAG_DESC': input_tag.description,
            'TAG_COUNT': input_tag.count,
        }
        if support_search:
            result['TAG_SEARCH_SUPPORT'] = {
                'SEARCH_ID': 'tagsearchbox',
                'ESC_TAG_NAME': escape_js_string(input_tag.name.replace(' ', '_'))
            }
        return result

    if not isinstance(tags, List):
        return parse(tags)

    output_rows = []
    for tag in tags:
        output_rows.append(parse(tag))
    return output_rows
