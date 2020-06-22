import sqlite3
from os import path, makedirs
from os.path import splitext, dirname
from typing import List, Tuple
import math
from PIL import Image


def create_thumbnail_image(img, thumb_bound=256):
    copy = img.copy()
    copy.thumbnail((thumb_bound, thumb_bound))
    return copy


def can_thumbnail_image(img, thumb_bound=256):
    return not (img.width <= thumb_bound and img.height <= thumb_bound)


def create_thumbnails(img: Image, img_path: str, thumb_bounds: List[int]) -> None:
    img_name, img_ext = splitext(img_path)
    for i in range(0, len(thumb_bounds)):
        bound = thumb_bounds[i]
        if can_thumbnail_image(img, bound):
            save_path = img_name + ".thumb_" + str(bound) + img_ext
            thumb = create_thumbnail_image(img, bound)
            thumb.save(save_path)
            thumb.close()


def create_and_save_thumbnail(img: Image, img_path: str, thumbsize: int) -> None:
    img_name, img_ext = splitext(img_path)
    save_path = img_name + ".thumb_" + str(thumbsize) + img_ext
    thumb = create_thumbnail_image(img, thumbsize)
    thumb.save(save_path)
    thumb.close()


def nextpow2(num: int) -> int:
    value = math.log2(num)
    value = math.ceil(value)
    return int(math.pow(2, value))


def lastpow2(num: int) -> int:
    value = math.log2(num)
    value = math.floor(value)
    return int(math.pow(2, value))


def create_all_pow_thumbnails(img: Image, img_path: str, min_size: int) -> None:
    min_pow2_size = nextpow2(min_size)
    img_size = max(img.width, img.height)
    max_pow2_size = lastpow2(img_size)
    sizes = []
    size = min_pow2_size
    while size <= max_pow2_size:
        sizes.append(size)
        size *= 2
    for i in range(0, len(sizes)):
        create_and_save_thumbnail(img, img_path, sizes[i])
    return None


def enforce_dirs_exists(file_path: str):
    try:
        dir_path = dirname(file_path)
        makedirs(dir_path)
    except FileExistsError:
        pass


def convert_to_imageset(img: Image, save_path: str) -> None:
    save_name, ext = splitext(save_path)

    def get_thumbnail_size(scale):
        return img.width * scale, img.height * scale

    def get_img_name(name: str):
        return path.join(f"{save_name}", f"{name}{ext}")

    def helper(name: str, scale=1.0, size=None):
        with img.copy() as copy:
            path = get_img_name(name)

            if size is None and scale != 1.0:
                size = get_thumbnail_size(scale)
            if size is not None:
                copy.thumbnail(size)

            enforce_dirs_exists(path)
            copy.save(path)

    helper("hirez", 1)
    helper("midrez", 0.5)
    helper("lorez", 0.25)
    helper("thumb", size=(256, 256))


def convert_db_images(db_path: str):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute(f"SELECT img_path FROM images")
    results = cursor.fetchall()
    for img_data in results:
        img_path = img_data[0]
        with Image.open(img_path) as img:
            convert_to_imageset(img, img_path)
    con.close()


# Debug Code
if __name__ == "__main__":
    #    convert_db_images("imgserver.db")
    pass

# Based on illustrators export png
# 300 HI REZ (1/1) RAW
# 150 MED REZ (1/2)
# 72 LOW REZ ~(1/4)
# 256x256 Thumbnail
