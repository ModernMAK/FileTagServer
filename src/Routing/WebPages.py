from typing import Dict, Optional, Tuple, Union, Callable, List, Set

from PIL import Image
from litespeed import serve, route, register_error_page
from pystache import Renderer

import src.PathUtil as PathUtil
import src.DbMediator as DbUtil
import src.API.ModelClients as Clients
import src.API.Models as Models

# define renderer
from src.API import ApiClients

renderer = None
db_path = PathUtil.data_path('mediaserver.db')


def escape_js_string(input: str) -> str:
    input = input.replace('/', '//')
    input = input.replace("'", '/')
    input = input.replace('"', '/"')
    return input


# hardcoded for now
def add_routes():
    global renderer
    renderer = Renderer(search_dirs=PathUtil.html_path("templates"))
    route(r"/", f=index, methods=['GET'])
    route(r"show/image/index", f=show_image_index, methods=['GET'])
    route(r"show/image/index/(\d*)", f=show_image_index_paged, methods=['GET'])
    route(r"show/image/(\d*)", f=show_image, methods=['GET'])
    route(r"show/image/(\d*)/edit", f=show_image_edit, methods=['GET'])
    route(r"show/tag/index", f=show_tag_index, methods=['GET'])
    route(r"show/tag/index/(\d*)", f=show_tag_index_paged, methods=['GET'])
    route(r"show/tag/(\d*)/", f=show_tag, methods=['GET'])
    route(r"show/tag/(\d*)/edit", f=show_tag_edit, methods=['GET'])

    route(r"show/upload/image", f=show_image_upload, methods=['GET'])
    route(r"action/upload_image", f=action_image_upload, methods=['POST'])
    route(r"action/update_tags/(\d*)", f=action_update_tags, methods=['POST'])
    route(r"action/image/search", f=action_image_search, methods=['POST'])


def index(request):
    return show_image_index(request)


def show_image_index(request):
    return show_image_index_paged(request, 0)


def show_image_index_paged(request, page: int):
    desired_file = PathUtil.html_image_path("index.html")
    image_client = Clients.ImagePost(db_path=db_path)
    req_imgs = image_client.get(page_size=50, offset=50 * page)

    img_context = parse_rest_image(req_imgs, 'thumb')
    tags = get_unique_tags(req_imgs)
    tag_context = parse_rest_tags(tags, support_search=True)
    context = {
        'TITLE': "Title",
        'IMG_LIST': img_context,
        'TAG_LIST': tag_context,
    }
    return serve_formatted(desired_file, context)


# @route("show/image/search/([\w%'\s]*)", no_end_slash=True)
def show_image_list_search(request, search: str):
    return show_image_list_paged_search(request, 0, search)


# @route(f"show/image/search/(\d*)/([\w%'\s]*)", no_end_slash=True)
def show_image_list_paged_search(request, page: int, search: str):
    desired_file = PathUtil.html_image_path("index.html")
    req_imgs = DbUtil.search_imgs(search, 50, page)
    img_id_list = []

    req_tags = DbUtil.get_imgs_tags_from_imgs(req_imgs)

    img_context = parse_rest_image(req_imgs)
    tag_context = parse_rest_tags(req_tags, support_search=True)
    context = {
        'TITLE': "Title",
        'IMG_LIST': img_context,
        'TAG_LIST': tag_context,
        'SEARCH': search,
    }
    return serve_formatted(desired_file, context)


def show_image(request, img_id):
    desired_file = PathUtil.html_image_path("page.html")
    img_data = DbUtil.get_img(img_id)
    if not img_data:
        return serve_error(404)
    tag_data = DbUtil.get_img_tags(img_id)
    img_context = parse_rest_image(img_data)[0]
    context = {
        'TITLE': "Title",
        'TAG_LIST': parse_rest_tags(tag_data, support_search=True)
    }
    context.update(img_context)
    return serve_formatted(desired_file, context)


def show_image_edit(request, img_id):
    desired_file = PathUtil.html_image_path("edit.html")
    img_data = DbUtil.get_img(img_id)
    if not img_data:
        return serve_error(404)
    tag_data = DbUtil.get_img_tags(img_id)

    img_ext, img_w, img_h = img_data
    context = {
        'TITLE': "Title",
        'TAG_LIST': parse_rest_tags(tag_data)
    }
    context.update(parse_rest_image(img_data))
    return serve_formatted(desired_file, context)


def show_tag_index(request):
    return show_tag_index_paged(request, 0)


def parse_rest_image(imgs: Union[Models.ImagePost, List[Models.ImagePost]], mip_name) -> Union[
    Dict[str, object], List[Dict[str, object]]]:
    def parse(input_img: Models.ImagePost):
        mip = input_img.mipmap.get_mip_by_name(mip_name)
        return {
            'PAGE_PATH': f"/show/image/{input_img.image_post_id}",
            'IMG_PATH': f'/file/{mip.file_id}',
            'IMG_ALT': f'{input_img.description}',
            'IMG_HEIGHT': mip.height,
            'IMG_WIDTH': mip.width,
            'IMG_ID': input_img.image_post_id,
            'IMG_EXT': mip.extension
        }

    if not isinstance(imgs, List):
        return parse(imgs)

    output_rows = []
    for img in imgs:
        output_rows.append(parse(img))
    return output_rows


def get_unique_tags(imgs: Union[Models.ImagePost, List[Models.ImagePost]]) -> List[Models.Tag]:
    def parse(input_img: Models.ImagePost) -> Set[Models.Tag]:
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
    desired_file = PathUtil.html_tag_path("index.html")
    rows = DbUtil.get_tags(50, page)

    fixed_rows = parse_rest_tags(rows)
    context = {'TITLE': "Tags",
               'TAG_LIST': fixed_rows}
    return serve_formatted(desired_file, context)


def show_tag(request, tag_id):
    desired_file = PathUtil.html_tag_path("page.html")
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
    desired_file = PathUtil.html_path("upload.html")
    return serve(desired_file)


def action_image_upload(request):
    desired_file = PathUtil.html_path("redirect.html")
    req = request['FILES']
    last_id = None
    for temp in req:
        filename, filestream = req[temp]
        img = Image.open(filestream)
        img_id = DbUtil.add_img(filename, img, PathUtil.image_path("posts"))
        img.close()
        last_id = img_id
    if last_id is not None:
        return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{last_id}"}, )


def action_update_tags(request, img_id: int):
    desired_file = PathUtil.html_path("redirect.html")
    req = request['POST']
    tag_box = req['tags']
    lines = tag_box.splitlines()
    for i in range(0, len(lines)):
        lines[i] = lines[i].strip()
    DbUtil.add_missing_tags(lines)
    DbUtil.set_img_tags(img_id, lines)
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{img_id}"}, )


def action_image_search(request):
    desired_file = PathUtil.html_path("redirect.html")
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
    return serve_formatted(PathUtil.html_path(f"error/{error_path}.html"), context)


@register_error_page(404)
def error_404(request, *args, **kwargs):
    return serve_formatted(PathUtil.html_path(f"error/{404}.html"))
