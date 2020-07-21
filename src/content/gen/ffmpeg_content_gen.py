import os
import ffmpeg
from io import BytesIO
from typing import List, Tuple

from src.content.content_gen import DynamicContentGenerator
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
            if 'thumbnail' in kwargs:
                output_args['vframes'] = kwargs['thumbnail'].get('frames', 1)

            m_out = m_in.output('pipe:', **output_args)

            proccess = m_out.run_async(pipe_stdout=True, pipe_stdin=True, pipe_stderr=True)
            std_out, std_err = proccess.communicate()
            if std_err is not None:
                raise Exception(std_err)
            output.write(std_out)

            return super().generate(output,**kwargs)
