from io import BytesIO
from pathlib import PurePath, Path
from typing import BinaryIO, Tuple

import PIL
from PIL import Image as ImageIO
from PIL.Image import Image
from contextlib import contextmanager

from FileTagServer.DBI.models import File


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


def generate_image_preview(local_file: str, stream: BinaryIO):
    # TODO handle non webp convertable formats
    with ImageIO.open(local_file) as img:
        shrink_image(img, 256, 256)
        img.save(stream, format="webp")


def supports_preview(mimetype: str) -> bool:
    if mimetype is None:
        return False
    major, minor = mimetype.split("/")
    if major == "image":
        return True
    else:
        return False


class PreviewManager:
    def __init__(self, preview_dir: str):
        self.__root = Path(preview_dir)
        self.__root.mkdir(parents=True,exist_ok=True)

    def get_path(self, id: int) -> Tuple[Path, Path]:
        gen_folder_id = int(id / 100)
        folder = self.__root / str(gen_folder_id)
        file = folder / str(id)
        file = file.with_suffix(".webp")
        return folder, file

    @staticmethod
    def _generate_image_preview(file: File, folder_path: Path, file_path: Path):
        folder_path.mkdir(exist_ok=True)
        try:
            with open(file_path, "wb") as stream:
                generate_image_preview(file.path, stream)
        except (PIL.UnidentifiedImageError, PIL.Image.DecompressionBombError):
            file_path.unlink(missing_ok=True)

    def generate_preview(self, file: File):
        if not supports_preview(file.mime):
            raise NotImplementedError()
        folder_path, file_path = self.get_path(file.id)
        self._generate_image_preview(file, folder_path, file_path)

    def get_preview_path(self, file: File) -> Path:
        _, file = self.get_path(file.id)
        return file
