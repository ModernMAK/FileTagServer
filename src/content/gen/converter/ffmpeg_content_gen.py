import os
from subprocess import PIPE, Popen

import ffmpeg
from io import BytesIO
from src.content.gen.content_gen import GeneratorFunction
from src.util import path_util


class FfmpegConverter:
    FFMPEG_PATH = os.path.join(path_util.project_root(), 'depends', 'ffmpeg', 'bin')
    FFMPEG_CMD = os.path.join(FFMPEG_PATH, "ffmpeg.exe")

    def convert_bytes(cls, input: BytesIO, output: BytesIO, **kwargs):
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

            # We manually specify command because of custom install
            # Otherwise we have to specify path
            # Id prefer to avoid this if only so i can quickly debug on multiple machines
            args = m_out.get_args()
            args = [cls.FFMPEG_CMD, *args]
            try:
                process = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                std_out, std_err = process.communicate(input=input.read())
                if std_err is not None:
                    raise Exception(std_err)
                output.write(std_out)
                process.kill()
            except Exception:
                process.kill()
                raise


def get_video_thumbnail_function(format: str, thumbnail_size=(128, 128)) -> GeneratorFunction:
    # Far as i can tell, only png and jpeg supported, webp might be since webm works
    # for more options, we should pipe to pil
    def thumbnail_function(input: BytesIO, output: BytesIO):
        FfmpegConverter.convert_bytes(input, output, format=format, frames=1, thumbnail=thumbnail_size)

    return thumbnail_function


# ... There is no audio thumbnail... its audio...

# Both audio and video have the same viewable function
def get_viewable_function(format: str) -> GeneratorFunction:
    def viewable_function(input: BytesIO, output: BytesIO):
        FfmpegConverter.convert_bytes(input, output, format=format)

    return viewable_function

