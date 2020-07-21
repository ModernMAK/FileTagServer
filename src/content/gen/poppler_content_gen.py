import shutil
from io import BytesIO
from typing import List, Tuple, Union

from PIL.Image import Image

from src.util import path_util
import os.path
from pdf2image import pdf2image

from src.content.content_gen import StaticContentGenerator, GeneratedContentType, DynamicContentGenerator, \
    SimpleContentGenerator


class DynamicPdfContentGenerator(DynamicContentGenerator):
    POPPLER_PATH = os.path.join(path_util.project_root(), 'depends', 'poppler', 'bin'),

    def generate(self, file: BytesIO, **kwargs) -> List[bytes]:
        if all(['format', 'pdf_format'] not in kwargs):
            return super().generate(file, **kwargs)

        with BytesIO() as output:
            pdf_format = kwargs.get('pdf_format', 'jpeg')
            format = kwargs.get('format', pdf_format)
            # w, h = kwargs.get('thumbnail')
            image = pdf2image.convert_from_bytes(
                file,
                dpi=72,
                fmt=pdf_format,
                poppler_path=self.POPPLER_PATH,
                single_file=True,
                strict=True
            )
            if 'thumbnail' in kwargs:
                w, h = kwargs.get('thumbnail')
                image.thumbnail(w, h)
            image.save(output, format=format)
            return super().generate(output, **kwargs)


class SimplePdfContentGenerator(SimpleContentGenerator):
    def __init__(self):
        self.backing_generator = DynamicPdfContentGenerator()

    def _generate_thumbnail(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        results = self.backing_generator.generate(file, format='webp', thumbnail=(128, 128))
        return results[0], 'webp'  # Returns one range, the whole file

    def _generate_viewable(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        # PDFS should never be converted into a viewable, as they are embeds
        return None


class DocumentContentGenerator(StaticContentGenerator):

    @staticmethod
    def get_supported_types() -> List[str]:
        # Supports pdf-like files
        return ['pdf', 'ai']

    @staticmethod
    def __get_thumbnail_ext(ext: str) -> str:
        return 'jpeg'

    @staticmethod
    def __get_viewable_ext(ext: str) -> str:
        return 'pdf'

    def generate(self, source_path: str, dest_folder: str, **kwargs):
        ext = path_util.get_formatted_ext(source_path)
        thumbnail_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.Thumbnail, ext))
        viewable_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.Viewable, ext))
        local_copy_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.LocalCopy, ext))

        if all(os.path.exists(path) for path in [thumbnail_path, viewable_path, local_copy_path]) and not kwargs.get(
                'rebuild', False):
            return

        if not os.path.exists(thumbnail_path) or kwargs.get('rebuild', False):
            thumbnails = pdf2image.convert_from_path(
                dpi=72,
                pdf_path=source_path, output_file=thumbnail_path,
                fmt=DocumentContentGenerator.__get_thumbnail_ext(ext),
                poppler_path=os.path.join(path_util.project_root(), 'depends', 'poppler', 'bin'),
                single_file=True, strict=True
            )
            thumbnail = thumbnails[0]
            thumbnail.thumbnail((256, 256))
            thumbnail.save(thumbnail_path)
            thumbnail.close()

        if not os.path.exists(viewable_path) or kwargs.get('rebuild', False):
            shutil.copyfile(source_path, viewable_path)

        if not os.path.exists(local_copy_path) or kwargs.get('rebuild', False):
            shutil.copyfile(source_path, local_copy_path)

    def get_file_name(self, content_type: GeneratedContentType, source_ext: str):
        if content_type is GeneratedContentType.Thumbnail:
            content_ext = DocumentContentGenerator.__get_thumbnail_ext(source_ext)
            return f"Thumbnail.{content_ext}"
        if content_type is GeneratedContentType.LocalCopy:
            return f"LocalCopy.{source_ext}"
        if content_type is GeneratedContentType.Viewable:
            content_ext = DocumentContentGenerator.__get_viewable_ext(source_ext)
            return f"Viewable.{content_ext}"
