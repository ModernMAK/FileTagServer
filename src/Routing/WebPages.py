from typing import Dict, Optional, Tuple, Union, Callable, List, Set

from PIL import Image
from litespeed import serve, route, register_error_page
from pystache import Renderer

import src.PathUtil as PathUtil
import src.API.ModelClients as Clients
import src.API.Models as Models
from src import DatabaseSearch
from src.DbUtil import Conwrapper, create_value_string, convert_tuple_to_list, create_entry_string
from src.Routing.REST import database_path
from src.dbmaintanence import get_legal_image_ext

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
    route(r"show/image/index", f=show_image_index, methods=['GET'])
    route(r"show/image/index/(\d*)", f=show_image_index_paged, methods=['GET'])
    route(r"show/image/(\d*)", f=show_image, methods=['GET'])
    route(r"show/image/(\d*)/edit", f=show_image_edit, methods=['GET'])
    route(r"show/tag/index", f=show_tag_index, methods=['GET'])
    route(r"show/tag/index/(\d*)", f=show_tag_index_paged, methods=['GET'])
    route(r"show/tag/(\d*)/", f=show_tag, methods=['GET'])
    route(r"show/tag/(\d*)/edit", f=show_tag_edit, methods=['GET'])
    route(r"show/image/search/(.*)", f=show_image_list_search, no_end_slash=True, methods=['GET'])
    route(r"show/image/search/(\d*)/(.*)",f=show_image_list_paged_search, no_end_slash=True)
    route(r"show/upload/image", f=show_image_upload, methods=['GET'])
    route(r"action/upload_image", f=action_image_upload, methods=['POST'])
    route(r"action/update_tags/(\d*)", f=action_update_tags, methods=['POST'])
    route(r"action/image/search", f=action_image_search, methods=['POST'])


def escape_js_string(input: str) -> str:
    input = input.replace('/', '//')
    input = input.replace("'", '/')
    input = input.replace('"', '/"')
    return input


def index(request):
    return show_image_index(request)


def show_image_index(request):
    return show_image_index_paged(request, 0)


def show_image_index_paged(request, page: int):
    page = int(page)
    page_size = 75
    desired_file = PathUtil.html_image_real_path("index.html")
    image_client = Clients.FilePage(db_path=db_path)
    req_imgs = image_client.get(page_size=page_size, offset=page_size * page)

    img_context = parse_rest_file(req_imgs, 'thumbnail')
    tags = get_unique_tags(req_imgs)
    tag_context = parse_rest_tags(tags, support_search=True)
    context = {
        'TITLE': "Title",
        'FILES': img_context,
        'TAG_LIST': tag_context,
    }
    return serve_formatted(desired_file, context)


# @route("show/image/search/([\w%'\s]*)", no_end_slash=True)
def show_image_list_search(request, search: str):
    return show_image_list_paged_search(request, 0, search)


# @route(f"show/image/search/(\d*)/([\w%'\s]*)", no_end_slash=True)
def show_image_list_paged_search(request, page: int, search: str):
    desired_file = PathUtil.html_image_real_path("index.html")
    items = search.split()
    for i in range(len(items)):
        items[i] = items[i].replace('_',' ')
    search_groups = DatabaseSearch.create_simple_search_groups(items)
    query = DatabaseSearch.create_query_from_search_groups(search_groups)
    with Conwrapper(db_path=db_path) as (conn, cursor):
        paged_query = f"{query} LIMIT 50 OFFSET {page * 50}"
        cursor.execute(paged_query)
        results = cursor.fetchall()
    ids = convert_tuple_to_list(results)
    file_client = Clients.FilePage(db_path=db_path)
    req_imgs = file_client.get(page_ids=ids)

    img_context = parse_rest_file(req_imgs, 'thumbnail')
    tags = get_unique_tags(req_imgs)
    tag_context = parse_rest_tags(tags, support_search=True)
    context = {
        'TITLE': "Title",
        'FILES': img_context,
        'TAG_LIST': tag_context,
        'SEARCH': search,
    }
    return serve_formatted(desired_file, context)


def show_image(request, img_id):
    image_client = Clients.FilePage(db_path=db_path)
    req_imgs = image_client.get(ids=[img_id])
    if req_imgs is None or len(req_imgs) < 1:
        return serve_error(404)
    req_imgs = req_imgs[0]
    img_context = parse_rest_file(req_imgs, 'full_rez')
    tag_context = parse_rest_tags(req_imgs.tags, support_search=True)

    desired_file = PathUtil.html_image_real_path("page.html")
    context = {
        'TITLE': "Title",
        'TAG_LIST': tag_context
    }
    context.update(img_context)
    return serve_formatted(desired_file, context)


def show_image_edit(request, img_id):
    image_client = Clients.FilePage(db_path=db_path)
    req_imgs = image_client.get(ids=[img_id])
    if req_imgs is None or len(req_imgs) < 1:
        return serve_error(404)
    req_imgs = req_imgs[0]
    img_context = parse_rest_file(req_imgs, 'full_rez')
    tag_context = parse_rest_tags(req_imgs.tags, support_search=True)

    desired_file = PathUtil.html_image_real_path("edit.html")
    context = {
        'TITLE': "Title",
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
            'PAGE_PATH': f"/show/image/{file_page.file_page_id}",
            'PAGE_ID': file_page.page_id,
            'FILE_PAGE_ID': file_page.file_page_id
        }
        alt = ''
        if file_page.description is not None:
            alt = str(file_page.description)

        if file_page.file.extension.lower() in get_legal_image_ext():
            base['IMG'] = \
                {
                    'PATH': PathUtil.dynamic_generated_virtual_path(
                        f"file/{file_page.file.file_id}/{image_file_name}.{file_page.file.extension}"),
                    'ALT': f'{alt}'
                }
        else:
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


def show_tag_index_paged(request, page: int):
    desired_file = PathUtil.html_tag_real_path("index.html")
    rows = DbUtil.get_tags(50, page)

    fixed_rows = parse_rest_tags(rows)
    context = {'TITLE': "Tags",
               'TAG_LIST': fixed_rows}
    return serve_formatted(desired_file, context)


def show_tag(request, tag_id):
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


def show_image_upload(request):
    desired_file = PathUtil.html_real_path("upload.html")
    return serve(desired_file)


def action_image_upload(request):
    desired_file = PathUtil.html_real_path("redirect.html")
    req = request['FILES']
    last_id = None
    for temp in req:
        filename, filestream = req[temp]
        img = Image.open(filestream)
        img_id = DbUtil.add_img(filename, img, PathUtil.image_real_path("posts"))
        img.close()
        last_id = img_id
    if last_id is not None:
        return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{last_id}"}, )


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
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{file_id}"}, )


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


def action_image_search(request):
    desired_file = PathUtil.html_real_path("redirect.html")
    req = request['POST']
    search = req['search']
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/search/{search}"}, )


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
