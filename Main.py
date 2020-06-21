from os.path import dirname, join, splitext
from litespeed import serve, route, start_with_args
from typing import Optional, Tuple, List, Dict, Union, Any, Iterable
from pystache import Renderer
from PIL import Image
import sqlite3

if __name__ == '__main__':
    renderer = Renderer()
    database_path = 'imgserver.db'


    def initialize_db():
        con = sqlite3.connect(database_path)
        cursor = con.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS images(img_id integer PRIMARY KEY AUTOINCREMENT, img_path text, img_width integer, img_height integer )")
        cursor.execute("CREATE TABLE IF NOT EXISTS tags(tag_id integer PRIMARY KEY AUTOINCREMENT, tag_name text)")
        con.commit()
        con.close()


    def add_img(img_path, img, root_path):
        # open
        con = sqlite3.connect(database_path)
        cursor = con.cursor()
        # insert
        cursor.execute(f"INSERT INTO images(img_width, img_height) VALUES({img.width},{img.height})")
        img_id = cursor.lastrowid
        # fix filepath
        _, img_ext = splitext(img_path)
        img_full_path = join(root_path, str(img_id) + img_ext)
        # save file, update table
        cursor.execute(f"UPDATE images SET img_path='{img_full_path}' where img_id={img_id}")
        img.save(img_full_path)
        # Close
        con.commit()
        con.close()
        return img_id


    def get_img(img_id):
        con = sqlite3.connect(database_path)
        cursor = con.cursor()
        cursor.execute(f"SELECT img_path, img_width, img_height FROM images WHERE img_id = {img_id}")
        row = cursor.fetchone()
        con.close()
        return row


    def get_imgs(count, offset=0):
        con = sqlite3.connect(database_path)
        cursor = con.cursor()
        cursor.execute(
            f"SELECT img_id, img_path, img_width, img_height FROM images ORDER BY img_id DESC LIMIT {count} OFFSET {offset}")
        rows = cursor.fetchall()
        con.close()
        return rows


    @route()
    def index(request):
        return show_post_list(request)


    @route("stylesheets/(.*)")
    def stylesheets(request, file):
        return serve(f"stylesheets/{file}")


    @route("images/dynamic/(.*)")
    def dynamic_images(request, file):
        return serve(f"images/dynamic/{file}")


    @route("images/static/(.*)")
    def static_images(request, file):
        return serve(f"images/static/{file}")


    @route("show/image/index")
    def show_post_list(request):
        desired_file = "html/imageIndexPage.html"
        rows = get_imgs(50)

        def parse_rows(input_rows):
            output_rows = []
            for temp_row in input_rows:
                img_id, temp_path, temp_w, temp_h = temp_row
                temp_dict = {
                    'PAGE_PATH': f"/show/image/{img_id}",
                    'IMG_HEIGHT': temp_h,
                    'IMG_WIDTH': temp_w,
                    'IMG_PATH': temp_path}
                output_rows.append(temp_dict)
            return output_rows

        fixed_rows = parse_rows(rows)
        context = {'TITLE': "Title",
                   'IMG_LIST': fixed_rows}
        return serve_formatted(desired_file, context)


    @route("show/image/(\d*)/")
    def show_post(request, id):
        desired_file = "html/imagePage.html"
        img_path, img_w, img_h = get_img(id)
        context = {'TITLE': "Title",
                   'IMG_ALT': "???",
                   'IMG_HEIGHT': img_h,
                   'IMG_WIDTH': img_w,
                   'IMG_PATH': img_path}
        return serve_formatted(desired_file, context)


    @route("show/image/(\d*)/edit")
    def show_post_edit(request, id):
        desired_file = "html/imagePage.html"
        img_path, img_w, img_h = get_img(id)
        context = {'TITLE': "Title",
                   'IMG_ALT': "???",
                   'IMG_HEIGHT': img_h,
                   'IMG_WIDTH': img_w,
                   'IMG_PATH': img_path}
        return serve_formatted(desired_file, context)

    @route("upload/image")
    def uploading_image(request):
        return serve("html/upload.html")


    @route("action/upload_image", methods=['POST'])
    def uploading_image(request):
        filename, filestream = request['FILES']['img']
        img = Image.open(filestream)
        img_id = add_img(filename, img, "images/dynamic")
        return serve_formatted("html/redirect.html", {"REDIRECT_URL": f"/show/image/{img_id}"}, )


    def serve_formatted(file: str, context: Dict[str, object], cache_age: int = 0,
                        headers: Optional[Dict[str, str]] = None, status_override: int = None) -> Tuple[
        bytes, int, Dict[str, str]]:
        content, status, header = serve(file, cache_age, headers, status_override)
        fixed_content = renderer.render(content, context)
        return fixed_content, status, header


    initialize_db()
    start_with_args()
