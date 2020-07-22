from io import BytesIO
from typing import List, Tuple, Union

from PIL import Image, ImageSequence

from src.content.content_gen import DynamicContentGenerator, SimpleContentGenerator


class DynamicImageContentGenerator(DynamicContentGenerator):
    def generate(self, file: BytesIO, **kwargs) -> List[bytes]:
        if kwargs.get('animated', False):
            return self._generate_animated(file, **kwargs)
        with Image.open(file) as file:
            with BytesIO() as output:
                output_kwargs = {}
                if 'format' in kwargs:
                    output_kwargs['format'] = kwargs['format']

                if 'thumbnail' in kwargs:
                    w, h = kwargs.get('thumbnail')
                    file.thumbnail(w, h)
                file.save(output, **output_kwargs)
                return super().generate(output, **kwargs)

    def _generate_animated(self, file: BytesIO, **kwargs):
        with Image.open(file) as file:
            result = []
            output_kwargs = {}
            if 'format' in kwargs:
                output_kwargs['format'] = kwargs['format']
            if 'loop' in kwargs:
                output_kwargs['loop'] = kwargs['loop']

            if 'duration' in kwargs:
                output_kwargs['duration'] = kwargs['duration']
            elif 'frames_per_Second' in kwargs:
                output_kwargs['duration'] = int(round(1000 / kwargs['frames_per_second']))

            thumbnail = kwargs.get('thumbnail', None)

            for frame in ImageSequence.Iterator(file):
                if thumbnail is None:
                    frame.thumbnail(thumbnail)
                result.append(frame)

            with BytesIO() as output:
                result[0].save(output,
                               save_all=True,
                               append_images=result[1:],
                               **output_kwargs)
                return super().generate(output, **kwargs)


class SimplePillowContentGenerator(SimpleContentGenerator):

    def __init__(self):
        self.backing_generator = DynamicImageContentGenerator()

    def _generate_thumbnail(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        # Dont generate thumbnails for SVGs
        if file_ext in ['svg']:
            return None
        results = self.backing_generator.generate(file, format='webp', thumbnail=(128, 128))
        return results[0], 'webp'  # Returns one range, the whole file

    def _generate_viewable(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        # Dont Generate Viewables for SVGs
        if file_ext in ['svg']:
            return None
        kwargs = {}
        if file_ext in ['gif']:
            kwargs['animated'] = True

        results = self.backing_generator.generate(file, format='webp', **kwargs)
        return results[0], 'webp'  # Returns one range, whole file
