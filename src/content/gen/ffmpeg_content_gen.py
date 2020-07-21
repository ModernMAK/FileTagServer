import os
import ffmpeg
from io import BytesIO
from typing import List, Tuple, Union

from src.content.content_gen import DynamicContentGenerator, SimpleContentGenerator
from src.util import path_util


class DynamicFfmpegContentGenerator(DynamicContentGenerator):
    FFMPEG_PATH = os.path.join(path_util.project_root(), 'depends', 'ffmpeg', 'bin'),

    # While range is supported, it is HIGHLY recommended, to not
    def generate(self, file: BytesIO, **kwargs) -> List[bytes]:
        if any(['format', 'thumbnail'] not in kwargs):
            return super().generate(file, **kwargs)
        with BytesIO() as output:
            m_in = ffmpeg.input('pipe:')
            output_args = {}
            if 'format' in kwargs:
                output_args['format'] = kwargs['format']
            if 'frames' in kwargs:
                output_args['vframes'] = kwargs['frames']
            if 'thumbnail' in kwargs:
                w, h = kwargs['thumbnail']
                output_args['scale'] = f"w={w}:h={h}:force_original_aspect_ratio=decrease"

            m_out = m_in.output('pipe:', **output_args)

            proccess = m_out.run_async(pipe_stdout=True, pipe_stdin=True, pipe_stderr=True)
            std_out, std_err = proccess.communicate()
            if std_err is not None:
                raise Exception(std_err)
            output.write(std_out)

            return super().generate(output, **kwargs)


class SimpleFfmpegContentGenerator(SimpleContentGenerator):
    def __init__(self):
        self.backing_generator = DynamicFfmpegContentGenerator()

    def _generate_thumbnail(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        results = self.backing_generator.generate(file, frames=1, format='webp', thumbnail=(128, 128))
        # Returns one range; the whole file, and it's extension
        return results[0], 'webp'

    def _generate_viewable(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        results = self.backing_generator.generate(file, format='webm')
        # Returns one range; the whole file, and it's extension
        return results[0], 'webm'
