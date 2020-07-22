import os.path
from io import BytesIO
from typing import List, Tuple, Union

from pdf2image import pdf2image

from src.content.content_gen import DynamicContentGenerator, SimpleContentGenerator
from src.util import path_util


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
