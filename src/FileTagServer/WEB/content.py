from io import BytesIO
from typing import BinaryIO

from PIL import Image as ImageIO
from PIL.Image import Image
from contextlib import contextmanager


@contextmanager
def shrink_image(img: Image, max_width: int = None, max_height: int = None) -> Image:

    aspect = img.width / img.height
    if max_height:
        h = img.height if img.height < max_height else max_height
    else:
        h = img.height
    # h's desired w
    w = h * aspect

    if max_width:
        dw = w if w < max_width else max_width
    else:
        dw = img.width if w > img.width else w
    # w's desired h
    dh = dw / aspect
    img.thumbnail((dw, dh))


def image_preview(local_file: str) -> BinaryIO:
    # TODO handle non webp convertable formats
    with ImageIO.open(local_file) as img:
        shrink_image(img, 256, 256)
        buffer = BytesIO()
        img.save(buffer, format="webp")
        return buffer

def supports_preview(mimetype:str) -> bool:
    if mimetype is None:
        return False
    major, minor = mimetype.split("/")
    if major == "image":
        return True
    else:
        return False
    pass