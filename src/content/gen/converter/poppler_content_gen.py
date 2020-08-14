import os.path
from io import BytesIO

from pdf2image import pdf2image

from src.content.gen.content_gen import GeneratorFunction
from src.util import path_util


def get_thumbnail_function(format: str, dpi=300, thumbnail_size=(128, 128)) -> GeneratorFunction:
    def thumbnail_function(input: BytesIO, output: BytesIO):
        PopplerConverter.convert_bytes(input, output, format=format, dbi=dpi, thumbnail=thumbnail_size)

    return thumbnail_function


# Pdf should already be viewable, so there is not get_viewable_function


# think poppler ONLY supports jpeg, tiff, png, and jbig2
# for more options, wed have to pipe

class PopplerConverter:
    POPPLER_PATH = os.path.join(path_util.project_root(), 'depends', 'poppler', 'bin')

    @classmethod
    def convert_bytes(cls, input: BytesIO, output: BytesIO, **kwargs):
        # For consistancy, allow format, or fmt by renaming format to fmt
        if 'format' in kwargs:
            kwargs['fmt'] = kwargs['format']
            del kwargs['format']

        # because size works differently than pil, we dont remap thumbnail to size
        image = pdf2image.convert_from_bytes(
            input,
            poppler_path=cls.POPPLER_PATH,
            strict=True,
            **kwargs
        )
        if 'thumbnail' in kwargs:
            w, h = kwargs.get('thumbnail')
            image.thumbnail(w, h)
        image.save(output)
