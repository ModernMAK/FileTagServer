import shutil
from io import BytesIO
from typing import List, Tuple

from src.util import path_util
from PIL import Image
from os.path import exists, join

from src.content.content_gen import StaticContentGenerator, GeneratedContentType, DynamicContentGenerator


class DynamicImageContentGenerator(DynamicContentGenerator):
    def generate(self, file: BytesIO, **kwargs) -> List[bytes]:
        format = kwargs.get('format')
        if format is None:
            return super().generate(file, **kwargs)

        with Image.open(file) as file:
            with BytesIO() as output:
                if 'thumbnail' in kwargs:
                    w, h = kwargs.get('thumbnail')
                    file.thumbnail(w, h)
                file.save(output, format=format)
                return super().generate(output, **kwargs)


class StaticImageContentGenerator(StaticContentGenerator):
    ignore_exts = ['svg']
    remap_exts = {}
    default_exts = 'webp'
    thumb_size =(256,256)

    @classmethod
    def get_proper_ext(cls, ext):
        if ext in cls.ignore_exts:
            return ext
        return cls.remap_exts.get(ext, cls.default_exts)  # Remap or use default

    def _generate_cache(self, file: BytesIO, content_type: GeneratedContentType, file_ext: str, **kwargs) -> bytes:
        with BytesIO() as output:
            with Image.open(file) as image:
                if content_type == GeneratedContentType.Thumbnail:
                    image.thumbnail(self.thumb_size)
                image.save(output)
            return output.getvalue()

    if not os.path.exists(viewable_path) or kwargs.get('rebuild', False):
        viewable = img.copy()
        viewable.save(viewable_path)
        viewable.close()



    # Just because a path exists does not mean it is used
    def get_path(self, cache_path: str, content_type: GeneratedContentType, file_ext: str):
        file_ext = self.get_proper_ext(file_ext)
        if content_type == GeneratedContentType.Thumbnail:
            return join(cache_path, f"Thumbnail.{file_ext}")
        elif content_type == GeneratedContentType.Viewable:
            return join(cache_path, f"Viewable.{file_ext}")

    @staticmethod
    def get_supported_types() -> List[str]:
        # Ripped from
        # https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html
        # Not all of these are correct
        return ['bmp', 'eps', 'gif', 'icns', 'ico', 'im', 'jpeg', 'jpg', 'j2p', 'jpx', 'msp', 'pcx', 'png', 'ppm',
                'spi', 'tiff', 'tif', 'webp', 'xbm', 'blp', 'cur', 'dds', 'fli', 'flc', 'fpx', 'ftex', 'gbr', 'gd',
                'imt', 'iptc', 'naa', 'mcidas', 'mic', 'mpp', 'pcd', 'pixar', 'pxr', 'psd', 'tga', 'wal', 'xpm']

    @staticmethod
    def __get_thumbnail_ext(ext: str) -> str:
        ignore = ['svg']
        if ext in ignore:
            return ext
        else:
            return 'webp'

    @staticmethod
    def __get_viewable_ext(ext: str) -> str:
        browser_support = ['png', 'jpeg', 'jpg', 'gif', 'svg', 'bmp', 'webp']
        if ext in browser_support:
            return ext
        else:
            return 'png'

    def generate(self, source_path: str, dest_folder: str, **kwargs):
        ext = path_util.get_formatted_ext(source_path)
        thumbnail_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.Thumbnail, ext))
        viewable_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.Viewable, ext))
        local_copy_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.LocalCopy, ext))

        if all(os.path.exists(path) for path in [thumbnail_path, viewable_path, local_copy_path]) and not kwargs.get(
                'rebuild', False):
            return

        with Image.open(source_path) as img:
            if not os.path.exists(thumbnail_path) or kwargs.get('rebuild', False):
                thumb = img.copy()
                thumb.thumbnail((256, 256))
                thumb.save(thumbnail_path)
                thumb.close()

            if not os.path.exists(viewable_path) or kwargs.get('rebuild', False):
                viewable = img.copy()
                viewable.save(viewable_path)
                viewable.close()

            if not os.path.exists(local_copy_path) or kwargs.get('rebuild', False):
                shutil.copyfile(source_path, local_copy_path)

    def get_file_name(self, content_type: GeneratedContentType, source_ext: str):
        if content_type is GeneratedContentType.Thumbnail:
            content_ext = ImageContentGenerator.__get_thumbnail_ext(source_ext)
            return f"Thumbnail.{content_ext}"
        if content_type is GeneratedContentType.LocalCopy:
            return f"LocalCopy.{source_ext}"
        if content_type is GeneratedContentType.Viewable:
            content_ext = ImageContentGenerator.__get_viewable_ext(source_ext)
            return f"Viewable.{content_ext}"
