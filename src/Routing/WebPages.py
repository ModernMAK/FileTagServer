import os
from math import ceil, floor
from typing import Dict, Optional, Tuple, Union, Callable, List, Set, Any

from PIL import Image
from litespeed import serve, route, register_error_page
from pystache import Renderer

import src.PathUtil as PathUtil
import src.API.ModelClients as Clients
import src.API.Models as Models
from src import DatabaseSearch
from src.Content.ContentGen import ImageContentGen, SvgContentGen
from src.DbUtil import Conwrapper, create_value_string, convert_tuple_to_list, create_entry_string

# define renderer
renderer = None
db_path = None


def initialize_module(**kwargs):
    global renderer
    global db_path
    config = kwargs.get('config', {})
    launch_args = config.get('Launch Args', {})
    search_dirs = launch_args.get('template_dirs', [PathUtil.html_real_path("templates")])
    renderer = Renderer(search_dirs=search_dirs)
    db_path = launch_args.get('db_path', PathUtil.data_real_path('mediaserver.db'))


# hardcoded for now
def add_routes():
    route(r"/", f=index, methods=['GET'])
    route(r"show/file/index", f=show_file_index, methods=['GET'])
    route(r"show/file/index/(\d*)", f=show_file_index_paged, methods=['GET'])
    route(r"show/file/(\d*)", f=show_file, methods=['GET'])
    route(r"show/file/(\d*)/edit", f=show_file_edit, methods=['GET'])
    route(r"show/tag/index", f=show_tag_index, methods=['GET'])
    route(r"show/tag/index/(\d*)", f=show_tag_index_paged, methods=['GET'])
    route(r"show/tag/(\d*)/", f=show_tag, methods=['GET'])
    route(r"show/tag/(\d*)/edit", f=show_tag_edit, methods=['GET'])
    route(r"show/file/search/(.*)", f=show_file_list_search, no_end_slash=True, methods=['GET'])
    route(r"show/file/search/(\d*)/(.*)", f=show_file_list_paged_search, no_end_slash=True)
    route(r"show/upload/file", f=show_file_upload, methods=['GET'])
    route(r"action/upload_file", f=action_file_upload, methods=['POST'])
    route(r"action/update_tags/(\d*)", f=action_update_tags, methods=['POST'])
    route(r"action/file/search", f=action_file_search, methods=['POST'])


def escape_js_string(input: str) -> str:
    input = input.replace('/', '//')
    input = input.replace("'", '/')
    input = input.replace('"', '/"')
    return input


def index(request):
    return show_file_index(request)


def show_file_index(request):
    return show_file_index_paged(request, 1)


def show_file_index_paged(request, page: int):
    def get_paged_path(local_page: int) -> str:
        return f"show/file/index/{local_page}"

    real_page = int(page) - 1
    if real_page < 0:
        return serve_error(404)
    page_size = 75
    desired_file = PathUtil.html_file_real_path("index.html")
    file_client = Clients.FilePage(db_path=db_path)
    req_imgs = file_client.get(page_size=page_size, offset=page_size * real_page)
    tot_imgs = file_client.count()
    if real_page > ceil(tot_imgs / page_size) - 1:
        return serve_error(404)
    img_context = parse_rest_file(req_imgs, 'thumbnail')
    tags = get_unique_tags(req_imgs)
    tags = tag_sort_by_count(tags)
    tag_context = parse_rest_tags(tags, support_search=True)

    page_context = parse_page_info(tot_imgs, page_size, page, get_paged_path)

    context = {
        'TITLE': "Title",
        'FILES': img_context,
        'TAG_LIST': tag_context,
    }
    context.update(page_context)
    return serve_formatted(desired_file, context)


# @route("show/file/search/([\w%'\s]*)", no_end_slash=True)
def show_file_list_search(request, search: str):
    return show_file_list_paged_search(request, 0, search)


# @route(f"show/file/search/(\d*)/([\w%'\s]*)", no_end_slash=True)
def show_file_list_paged_search(request, page: int, search: str):
    desired_file = PathUtil.html_file_real_path("index.html")
    items = search.split()
    for i in range(len(items)):
        items[i] = items[i].replace('_', ' ')
    search_groups = DatabaseSearch.create_simple_search_groups(items)
    query = DatabaseSearch.create_query_from_search_groups(search_groups)
    with Conwrapper(db_path=db_path) as (conn, cursor):
        paged_query = f"{query} LIMIT 50 OFFSET {real_page * 50}"
        cursor.execute(paged_query)
        results = cursor.fetchall()
    ids = convert_tuple_to_list(results)
    file_client = Clients.FilePage(db_path=db_path)
    req_imgs = file_client.get(page_ids=ids)

    img_context = parse_rest_file(req_imgs, 'thumbnail')
    tags = get_unique_tags(req_imgs)
    tags = tag_sort_by_count(tags)
    tag_context = parse_rest_tags(tags, support_search=True)
    context = {
        'TITLE': "Title",
        'FILES': img_context,
        'TAG_LIST': tag_context,
        'SEARCH': search,
    }
    return serve_formatted(desired_file, context)


def show_file_shared(request, img_id) -> Union[
    Tuple[bool, int], Tuple[bool, Tuple[Dict[str, Any], Dict[str, Any], Models.FilePage]]]:
    file_client = Clients.FilePage(db_path=db_path)
    req_imgs = file_client.get(ids=[img_id])
    if req_imgs is None or len(req_imgs) < 1:
        return False, 404
    req_imgs = req_imgs[0]
    img_context = parse_rest_file(req_imgs, 'full_rez')
    tag_context = parse_rest_tags(req_imgs.tags, support_search=True)
    return True, (img_context, tag_context, req_imgs)


def show_file(request, img_id):
    success, result = show_file_shared(request, img_id)
    if not success:
        return serve_error(result)
    img_context, tag_context, file = result

    desired_file = PathUtil.html_file_real_path("page.html")
    context = {
        'TITLE': file.name,
        'TAG_LIST': tag_context
    }
    context.update(img_context)
    return serve_formatted(desired_file, context)


def show_file_edit(request, img_id):
    success, result = show_file_shared(request, img_id)
    if not success:
        return serve_error(result)
    img_context, tag_context, file = result

    desired_file = PathUtil.html_file_real_path("edit.html")
    context = {
        'TITLE': file.name,
        'TAG_LIST': tag_context
    }
    context.update(img_context)
    return serve_formatted(desired_file, context)


def show_tag_index(request):
    return show_tag_index_paged(request, 0)


def parse_rest_file(file_pages: Union[Models.FilePage, List[Models.FilePage]], image_file_name: str) -> Union[
    Dict[str, object], List[Dict[str, object]]]:
    def parse(file_page: Models.FilePage):
        base = {
            'PAGE_PATH': f"show/file/{file_page.file_page_id}",
            'PAGE_ID': file_page.page_id,
            'FILE_PAGE_ID': file_page.file_page_id
        }
        alt = ''
        if file_page.description is not None:
            alt = str(file_page.description)

        use_file = False
        ext = file_page.file.extension.lower()
        if ext in ImageContentGen.static_get_supported():
            ext = ImageContentGen.static_get_retargeting().get(ext, ext)
            partial_path = f"file/{file_page.file.file_id}/{image_file_name}.{ext}"
            if os.path.exists(PathUtil.dynamic_generated_real_path(partial_path)):
                base['IMG'] = \
                    {
                        'PATH': PathUtil.dynamic_generated_virtual_path(partial_path),
                        'ALT': f'{alt}'
                    }
            else:
                use_file = True
        elif ext in SvgContentGen.static_get_supported():
            partial_path = f"file/{file_page.file.file_id}/full_rez.{ext}"
            if os.path.exists(PathUtil.dynamic_generated_real_path(partial_path)):
                base['IMG'] = \
                    {
                        'PATH': PathUtil.dynamic_generated_virtual_path(partial_path),
                        'ALT': f'{alt}'
                    }
            else:
                use_file = True
        else:
            use_file = True

        if use_file:
            base['FILE'] = \
                {
                    'EXTENSION': file_page.file.extension.upper(),
                    'ALT': f'{alt}'
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


def parse_page_info(items: int, page_size: int, current_page: int, get_page_path: Callable[[int], str], range_size: int = 5):
    pages = int(ceil(items / page_size))
    current_page = int(current_page)

    def get_pairs():
        symbols = []
        # Symbol, Link, Current
        CURRENT = 'active'
        DISABLED = 'disabled'

        if current_page != 1:
            symbols.append(('<<', 1, None))
        else:
            symbols.append(('<<', None, DISABLED))

        if current_page > 1:
            symbols.append(('<', current_page - 1, None))
        else:
            symbols.append(('<', None, DISABLED))

        if current_page > range_size + 1:
            symbols.append(('...', None, DISABLED))

        for i in range(current_page - range_size, current_page + range_size + 1):
            if 1 <= i <= pages:
                if i == current_page:
                    symbols.append((i, None, CURRENT))
                else:
                    symbols.append((i, i, None))

        if current_page < pages - range_size - 1:
            symbols.append(('...', None, DISABLED))

        if current_page < pages:
            symbols.append(('>', current_page + 1, None))
        else:
            symbols.append(('>', None, DISABLED))

        if current_page != pages:
            symbols.append(('>>', pages, None))
        else:
            symbols.append(('>>', None, DISABLED))
        return symbols

    context = []
    pairs = get_pairs()
    for pair in pairs:
        symbol, page, status = pair
        if page is None:
            local_context = {'RAW': {'SYMBOL': symbol, 'STATUS': status}}
        else:
            local_context = {'PAGE': {'PATH': get_page_path(page), 'SYMBOL': symbol, 'STATUS': status}}
        context.append(local_context)

    return {'PAGES': context}


def show_tag_index_paged(request, page: int):
    return serve_error(404)
    desired_file = PathUtil.html_tag_real_path("index.html")
    rows = DbUtil.get_tags(50, page)

    fixed_rows = parse_rest_tags(rows)
    context = {'TITLE': "Tags",
               'TAG_LIST': fixed_rows}
    return serve_formatted(desired_file, context)


def show_tag(request, tag_id):
    return serve_error(404)
    desired_file = PathUtil.html_tag_real_path("page.html")
    result = DbUtil.get_tag(tag_id)
    if not result:
        return serve_error(404)
    (tag_name,) = result

    context = {
        'PAGE_PATH': f"/show/tag/{tag_id}",
        'TAG_ID': tag_id,
        'TAG_NAME': tag_name,
    }
    return serve_formatted(desired_file, context)


def show_tag_edit(request, img_id):
    serve_error(404)


def show_file_upload(request):
    desired_file = PathUtil.html_real_path("upload.html")
    return serve(desired_file)


def action_file_upload(request):
    return serve_error(404)
    desired_file = PathUtil.html_real_path("redirect.html")
    req = request['FILES']
    last_id = None
    for temp in req:
        filename, filestream = req[temp]
        img = Image.open(filestream)
        img_id = DbUtil.add_img(filename, img, PathUtil.file_real_path("posts"))
        img.close()
        last_id = img_id
    if last_id is not None:
        return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/file/{last_id}"}, )


def action_update_tags(request, file_id: int):
    desired_file = PathUtil.html_real_path("redirect.html")
    req = request['POST']

    tag_box = req['tags']
    page_id = req['page_id']
    lines = tag_box.splitlines()
    for i in range(0, len(lines)):
        lines[i] = lines[i].strip()
    add_missing_tags(lines)
    set_img_tags(page_id, lines)
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/file/{file_id}"}, )


def add_missing_tags(tag_list: List[str]):
    with Conwrapper(db_path) as (con, cursor):
        values = create_value_string(tag_list)
        # Should be one execute, but this is easier to code
        # tag_name is a unique column, and should err if we insert an illegal value
        cursor.execute(f"INSERT OR IGNORE INTO tag(name) VALUES {values}")
        con.commit()


def set_img_tags(page_id: int, tag_list: List[str]) -> None:
    with Conwrapper(db_path) as (con, cursor):
        values = create_entry_string(tag_list)

        # Get tag_ids to set
        cursor.execute(f"SELECT id FROM tag WHERE name IN {values}")
        rows = cursor.fetchall()
        tag_id_list = convert_tuple_to_list(rows)
        tag_id_collection = create_entry_string(tag_id_list)
        cursor.execute(
            f"DELETE FROM tag_map where page_id = {page_id} and tag_id NOT IN {tag_id_collection}")

        pairs = []
        for tag_id in tag_id_list:
            pairs.append((page_id, tag_id))
        values = create_value_string(pairs)
        cursor.execute(f"INSERT OR IGNORE INTO tag_map (page_id, tag_id) VALUES {values}")

        con.commit()


def action_file_search(request):
    desired_file = PathUtil.html_real_path("redirect.html")
    req = request['POST']
    search = req['search']
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/file/search/{search}"}, )


def serve_formatted(file: str, context: Dict[str, object] = None, cache_age: int = 0,
                    headers: Optional[Dict[str, str]] = None,
                    status_override: int = None) -> Tuple[bytes, int, Dict[str, str]]:
    if context is None:
        context = {}

    content, status, header = serve(file, cache_age, headers, status_override)
    fixed_content = renderer.render(content, context)
    return fixed_content, status, header


def serve_error(error_path, context=None) -> Tuple[bytes, int, Dict[str, str]]:
    return serve_formatted(PathUtil.html_real_path(f"error/{error_path}.html"), context)


@register_error_page(404)
def error_404(request, *args, **kwargs):
    return serve_formatted(PathUtil.html_real_path(f"error/{404}.html"))
