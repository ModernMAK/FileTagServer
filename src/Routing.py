from typing import Dict, Optional, Tuple
from os.path import splitext, dirname
from litespeed import serve, route
from PIL import Image
from pystache import Renderer
import src.PathUtil as PathUtil
from src.DbUtil import add_img, get_imgs, get_img, get_img_tags, add_missing_tags, set_img_tags

# define renderer
renderer = Renderer()


# hardcoded for now
def initializeModule():
    global renderer
    renderer = Renderer()


@route("/debug(.*)")
def debug(request, path):
    return serve(PathUtil.html_path("album.html"))


@route("/")
def index(request):
    return show_post_list(request)


@route("css/(.*).map/")
def css_map(request, file):
    file = dirname(file) + ".map"
    desired_file = PathUtil.css_path(file)
    return serve(desired_file)


@route("css/(.*)")
def css(request, file):
    desired_file = PathUtil.css_path(file)
    content, code, headers = serve(desired_file)
    _, ext = splitext(file.strip('/'))
    if ext.lower() == ".css":
        headers['Content-Type'] = "text/css"
    return content, code, headers


@route("js/(.*).map/")
def javascript_map(request, file):
    file = dirname(file) + ".map"
    desired_file = PathUtil.js_path(file)
    return serve(desired_file)


@route("js/(.*)")
def javascript(request, file):
    desired_file = PathUtil.js_path(file)
    return serve(desired_file)


@route("images/(.*)")
def images(request, file):
    desired_file = PathUtil.image_path(file)
    return serve(desired_file)


@route("show/image/index")
def show_post_list(request):
    desired_file = PathUtil.html_path("imageIndexPage.html")
    rows = get_imgs(50)

    def parse_rows(input_rows):
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

    fixed_rows = parse_rows(rows)
    context = {'TITLE': "Title",
               'IMG_LIST': fixed_rows}
    return serve_formatted(desired_file, context)


@route("show/image/(\d*)/")
def show_post(request, img_id):
    desired_file = PathUtil.html_path("imagePage.html")
    img_data = get_img(img_id)
    if not img_data:
        return serve_error(404)
    tag_data = get_img_tags(img_id)

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
def show_post_edit(request, img_id):
    desired_file = PathUtil.html_path("imagePageEdit.html")
    img_data = get_img(img_id)
    if not img_data:
        return serve_error(404)
    tag_data = get_img_tags(img_id)

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


@route("upload/image")
def uploading_image(request):
    desired_file = PathUtil.html_path("upload.html")
    return serve(desired_file)


@route("action/upload_image", methods=['POST'])
def uploading_image(request):
    desired_file = PathUtil.html_path("redirect.html")
    req = request['FILES']
    filename, filestream = req['img']
    img = Image.open(filestream)
    img_id = add_img(filename, img, PathUtil.image_path("posts"))
    img.close()
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{img_id}"}, )


@route("action/update_tags/(\d*)", methods=['POST'])
def updating_tags(request, img_id: int):
    desired_file = PathUtil.html_path("redirect.html")
    req = request['POST']
    tag_box = req['tags']
    lines = tag_box.splitlines()
    for i in range(0, len(lines)):
        lines[i] = lines[i].strip()
    add_missing_tags(lines)
    set_img_tags(img_id, lines)
    return serve_formatted(desired_file, {"REDIRECT_URL": f"/show/image/{img_id}"}, )


def serve_formatted(file: str, context: Dict[str, object], cache_age: int = 0, headers: Optional[Dict[str, str]] = None,
                    status_override: int = None) -> Tuple[bytes, int, Dict[str, str]]:
    content, status, header = serve(file, cache_age, headers, status_override)
    fixed_content = renderer.render(content, context)
    return fixed_content, status, header


def serve_error(error_code) -> Tuple[bytes, int, Dict[str, str]]:
    result = serve(PathUtil.html_path(f"{error_code}.html"), status_override=error_code)
    if error_code != 404 and result[1] == 404:
        result = serve(PathUtil.html_path(f"{404}.html"), status_override=404)
    return result


# has to be loaded LAST
# Will capture EVERYTHING meant for declerations after it
@route("(.*)")
def catchall(request, catch):
    return serve_error(404)
