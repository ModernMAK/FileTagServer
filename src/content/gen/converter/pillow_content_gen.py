from io import BytesIO
from typing import Tuple

from PIL import Image, ImageSequence

from src.content.gen.content_gen import GeneratorFunction


def get_thumbnail_function(format: str, thumbnail_size: Tuple[int, int] = (128, 128),
                           animated=False) -> GeneratorFunction:
    if animated:
        def thumbnail_function(input: BytesIO, output: BytesIO):
            return PillowConvert.convert_animated_bytes(input, output, format=format, thumbnail=thumbnail_size)
    else:
        def thumbnail_function(input: BytesIO, output: BytesIO):
            return PillowConvert.convert_bytes(input, output, format=format, thumbnail=thumbnail_size)

    return thumbnail_function


def get_viewable_function(format: str, animated=False) -> GeneratorFunction:
    if animated:
        def viewable_function(input: BytesIO, output: BytesIO):
            return PillowConvert.convert_animated_bytes(input, output, format=format)
    else:
        def viewable_function(input: BytesIO, output: BytesIO):
            return PillowConvert.convert_bytes(input, output, format=format)

    return viewable_function


class PillowConvert:
    @staticmethod
    def convert_bytes(input: BytesIO, output: BytesIO, **kwargs):
        with Image.open(input) as image:
            if 'thumbnail' in kwargs:
                w, h = kwargs.get('thumbnail')
                del kwargs['thumbnail']
                image.thumbnail(w, h)

            image.save(output, **kwargs)

    @staticmethod
    def convert_animated_bytes(input: BytesIO, output: BytesIO, **kwargs):
        with Image.open(input) as image:
            if 'duration' not in kwargs:
                # Defaults to roughly 24 frames per second (1 second / 24 frames) = 42 milliseconds
                kwargs['duration'] = image.info.get('duration', 42)

            if 'loop' not in kwargs:
                kwargs['loop'] = image.info.get('loop', True)

            thumbnail = kwargs.get('thumbnail', None)
            del kwargs['thumbnail']

            frames = []
            for frame in ImageSequence.Iterator(image):
                if thumbnail is None:
                    frame.thumbnail(thumbnail)
                frames.append(frame)

            frames[0].save(output, save_all=True, append_images=frames[1:], **kwargs)
