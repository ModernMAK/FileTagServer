from typing import Dict, Optional, Tuple, Union, Callable

from PIL import Image
from litespeed import serve, route, register_error_page
from pystache import Renderer

import src.PathUtil as PathUtil
import src.DbUtil as DbUtil

# define renderer
renderer = None


def escape_js_string(input: str) -> str:
    input = input.replace('/', '//')
    input = input.replace("'", '/')
    input = input.replace('"', '/"')
    return input


# hardcoded for now
def init():
    global renderer
    renderer = Renderer(search_dirs=PathUtil.html_path("templates"))


@route("/debug(.*)")
def debug(request, path):
    return None
    return serve(PathUtil.html_path("bootstrap_template.html"))


@route("/")
def index(request):
    return show_image_list_index(request)


@route("show/image/index")
def show_image_list_index(request):
    return show_image_list(request, 0)


@route(f"show/image/index/(\d*)")
def show_image_list(request, page: int):
    desired_file = PathUtil.html_image_path("index.html")
    req_imgs = DbUtil.get_imgs(50, page)
    req_tags = DbUtil.get_imgs_tags(50, page)

    def parse_img_rows(input_rows):
        output_rows = []
        for temp_row in input_rows:
            img_id, temp_ext, temp_w, temp_h = temp_row
            temp_dict = {
                'PAGE_PATH': f"/show/image/{img_id}",
                'IMG_HEIGHT': temp_h,
                'IMG_WIDTH': temp_w,
                'IMG_ID': img_id,
                'IMG_EXT': temp_ext
            }
            output_rows.append(temp_dict)
        return output_rows

    def parse_tag_rows(input_rows):
        output_rows = []
        for temp_row in input_rows:
            tag_id, tag_name, tag_count = temp_row
            temp_dict = {
                'PAGE_PATH': f"/show/tag/{tag_id}",
                'TAG_COUNT': tag_count,
                'TAG_NAME': tag_name,
                'TAG_ID': tag_id,
                'TAG_SEARCH_SUPPORT': {
                    'SEARCH_ID': 'tagsearchbox',
                    'ESC_TAG_NAME': escape_js_string(tag_name.replace(' ', '_'))
                }
            }
            output_rows.append(temp_dict)
        return output_rows

    img_context = parse_img_rows(req_imgs)
    tag_context = parse_tag_rows(req_tags)
    context = {
        'TITLE': "Title",
        'IMG_LIST': img_context,
        'TAG_LIST': tag_context,
    }
    return serve_formatted(desired_file, context)


@route("show/image/search/([\w%'\s]*)", no_end_slash=True)
def show_image_list_search(request, search: str):
    return show_image_list_paged_search(request, 0, search)


@route(f"show/image/search/(\d*)/([\w%'\s]*)", no_end_slash=True)
def show_image_list_paged_search(request, page: int, search: str):
    desired_file = PathUtil.html_image_path("index.html")
    req_imgs = DbUtil.search_imgs(search, 50, page)
    img_id_list = []
    for img_id, _, _, _ in req_imgs:
        img_id_list.append(img_id)

    req_tags = DbUtil.get_imgs_tags_from_ids(img_id_list)

    def parse_img_rows(input_rows):
        output_rows = []
        for temp_row in input_rows:
            img_id, temp_ext, temp_w, temp_h = temp_row
            temp_dict = {
                'PAGE_PATH': f"/show/image/{img_id}",
                'IMG_HEIGHT': temp_h,
                'IMG_WIDTH': temp_w,
                'IMG_ID': img_id,
                'IMG_EXT': temp_ext
            }
            output_rows.append(temp_dict)
        return output_rows

    def parse_tag_rows(input_rows):
        output_rows = []
        for temp_row in input_rows:
            tag_id, tag_name, tag_count = temp_row
            temp_dict = {
                'PAGE_PATH': f"/show/tag/{tag_id}",
                'TAG_COUNT': tag_count,
                'TAG_NAME': tag_name,
                'TAG_ID': tag_id,
            }
            output_rows.append(temp_dict)
        return output_rows

    img_context = parse_img_rows(req_imgs)
    tag_context = parse_tag_rows(req_tags)
    context = {
        'TITLE': "Title",
        'IMG_LIST': img_context,
        'TAG_LIST': tag_context,
        'SEARCH': search,
    }
    return serve_formatted(desired_file, context)


@route(f"show/image/(\d*)")
def show_image(request, img_id):
    desired_file = PathUtil.html_image_path("page.html")
    img_data = DbUtil.get_img(img_id)
    if not img_data:
        return serve_error(404)
    tag_data = DbUtil.get_img_tags(img_id)

    def parse_tag_rows(input_rows):
        output_rows = []
        for temp_row in input_rows:
            tag_id, tag_name = temp_row
            temp_dict = {
                'TAG_ID': tag_id,
                'TAG_NAME': tag_name
            }
            output_rows.append(temp_dict)
        return output_rows

    img_ext, img_w, img_h = img_data
    context = {
        'TITLE': "Title",
        'IMG_ALT': "???",
        'IMG_HEIGHT': img_h,
        'IMG_WIDTH': img_w,
        'IMG_ID': img_id,
        'IMG_EXT': img_ext,
        'TAG_LIST': parse_tag_rows(tag_data)
    }
    return serve_formatted(desired_file, context)


@route("show/image/(\d*)/edit")
def show_image_edit(request, img_id):
    desired_file = PathUtil.html_image_path("edit.html")
    img_data = DbUtil.get_img(img_id)
    if not img_data:
        return serve_error(404)
    tag_data = DbUtil.get_img_tags(img_id)

    def parse_tag_rows(input_rows):
        output_rows = []
        for tag_id, tag_name in input_rows:
            temp_dict = {
                'TAG_ID': tag_id,
                'TAG_NAME': tag_name
            }
            output_rows.append(temp_dict)
        return output_rows

    img_ext, img_w, img_h = img_data
    context = {
        'TITLE': "Title",
        'IMG_ALT': "???",
        'IMG_HEIGHT': img_h,
        'IMG_WIDTH': img_w,
        'IMG_ID': img_id,
        'IMG_EXT': img_ext,
        'TAG_LIST': parse_tag_rows(tag_data)
    }
    return serve_formatted(desired_file, context)


@route("show/tag/index")
def show_tag_list_index(request):
    return show_tag_list(request, 0)


@route("show/tag/index/(\d*)")
def show_tag_list(request, page: int):
    desired_file = PathUtil.html_tag_path("index.html")
    rows = DbUtil.get_tags(50, page)

    def parse_rows(input_rows):
        output_rows = []
        for temp_row in input_rows:
            tag_id, tag_name = temp_row
            temp_dict = {
                'PAGE_PATH': f"/show/tag/{tag_id}",
                'TAG_ID': tag_id,
                'TAG_NAME': tag_name,
            }
            output_rows.append(temp_dict)
        return output_rows

    fixed_rows = parse_rows(rows)
    context = {'TITLE': "Tags",
               'TAG_LIST': fixed_rows}
    return serve_formatted(desired_file, context)


@route("show/tag/(\d*)/")
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
    # return serve_error(404)
    # desired_file = PathUtil.html_path("page.html")
    # img_data = DbUtil.get_img(img_id)
    # if not img_data:
    #     return serve_error(404)
    # tag_data = DbUtil.get_img_tags(img_id)
    #
    # def parse_tag_rows(input_rows):
    #     output_rows = []
    #     for temp_row in input_rows:
    #         tag_id, tag_name = temp_row
    #         temp_dict = {
    #             'TAG_ID': tag_id,
    #             'TAG_NAME': tag_name
    #         }
    #         output_rows.append(temp_dict)
    #     return output_rows
    #
    # img_ext, img_w, img_h = img_data
    # context = {
    #     'TITLE': "Title",
    #     'IMG_ALT': "???",
    #     'IMG_HEIGHT': img_h,
    #     'IMG_WIDTH': img_w,
    #     'IMG_ID': img_id,
    #     'IMG_EXT': img_ext,
    #     'TAG_LIST': parse_tag_rows(tag_data)
    # }
    # return serve_formatted(desired_file, context)


@route("show/tag/(\d*)/edit")
def show_tag_edit(request, img_id):
    serve_error(404)
    # desired_file = PathUtil.html_path("edit.html")
    # img_data = DbUtil.get_img(img_id)
    # if not img_data:
    #     return serve_error(404)
    # tag_data = DbUtil.get_img_tags(img_id)
    #
    # def parse_tag_rows(input_rows):
    #     output_rows = []
    #     for tag_id, tag_name in input_rows:
    #         temp_dict = {
    #             'TAG_ID': tag_id,
    #             'TAG_NAME': tag_name
    #         }
    #         output_rows.append(temp_dict)
    #     return output_rows
    #
    # img_ext, img_w, img_h = img_data
    # context = {
    #     'TITLE': "Title",
    #     'IMG_ALT': "???",
    #     'IMG_HEIGHT': img_h,
    #     'IMG_WIDTH': img_w,
    #     'IMG_ID': img_id,
    #     'IMG_EXT': img_ext,
    #     'TAG_LIST': parse_tag_rows(tag_data)
    # }
    # return serve_formatted(desired_file, context)


@route("upload/image")
def uploading_image(request):
    desired_file = PathUtil.html_path("upload.html")
    return serve(desired_file)


@route("action/upload_image", methods=['POST'])
def uploading_image(request):
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


@route("action/update_tags/(\d*)", methods=['POST'])
def updating_tags(request, img_id: int):
    desired_file = PathUtil.html_path("redirect.html")
    req = request['POST']
    tag_box = req['tags']
    lines = tag_box.splitlines()
    for i in range(0, len(lines)):
        lines[i] = lines[i].strip()
    DbUtil.add_missing_tags(lines)
    DbUtil.set_img_tags(img_id, lines)
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{img_id}"}, )


@route("action/image/search", methods=['POST'])
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


def serve_error(error_code) -> Tuple[bytes, int, Dict[str, str]]:
    result = serve(PathUtil.html_path(f"{error_code}.html"), status_override=error_code)
    if error_code != 404 and result[1] == 404:
        result = serve(PathUtil.html_path(f"{404}.html"), status_override=404)
    return result


@register_error_page(404)
def error_404(request, *args, **kwargs):
    return serve_formatted(PathUtil.html_path(f"error/{404}.html"))


# has to be loaded LAST
# Will capture EVERYTHING meant for declerations after it
@route("(.*)")
def catchall(request, catch):
    return serve_error(404)
