import mimetypes
from typing import List, Callable, Tuple
from src.content.gen.converter import poppler_content_gen, libre_office_content_gen, ffmpeg_content_gen, \
    pillow_content_gen
from src.content.gen.content_gen import FileConverter, MimeType, GeneratorFunction, pipe_generators
from src.content.gen.mimetype_util import MimeUtil


def convert_ext_to_format_mime_pairs(*extensions: str) -> List[Tuple[str, MimeType]]:
    mimes = []
    for ext in extensions:
        mime = mimetypes.guess_type(f'not a real file.{ext}')
        pair = (ext, mime)
        mimes.append(pair)
    return mimes


def register_helper(converter: FileConverter,
                    get_function: Callable[[str], GeneratorFunction],
                    allow_self_map=True, surpress_warning=False,
                    source_formats: List[str] = None, dest_formats: List[str] = None,
                    source_mimes: List[Tuple[str, MimeType]] = None, dest_mimes: List[Tuple[str, MimeType]] = None):
    if source_formats is None:
        source_formats = []
    if source_mimes is None:
        source_mimes = []
    if dest_formats is None:
        dest_formats = []
    if dest_mimes is None:
        dest_mimes = []

    source_mimes = [*convert_ext_to_format_mime_pairs(*source_formats), *source_mimes]
    dest_mimes = [*convert_ext_to_format_mime_pairs(*dest_formats), *dest_mimes]

    for source_index in range(len(source_formats)):
        source_mime = source_mimes[source_index]
        for dest_index in range(len(dest_formats)):
            dest_mime = dest_mimes[dest_index]
            dest_format = dest_formats[dest_index]

            if source_mime == dest_mime:
                if not surpress_warning:
                    print(f"{source_mime} mapped to itself! Was this intentional?")
                    print(f"\tSource: {source_formats[source_index]}")
                    print(f"\tDestenation: {dest_format}\n")
                    print(f"\t\tFor most cases; where only conversion is needed, this should not be done.")
                if not allow_self_map:
                    continue

            function = get_function(dest_format)
            converter.register(source_mime, dest_mime, function)


# FFMPEG ====================
def initialize_ffmpeg_thumbnail_gen(converter: FileConverter):
    source_formats = []  # ['mpv', 'ogv', 'mp4', 'avi', 'wmv', 'mov', *additional_sources]
    dest_formats = []  # ['png', 'jpeg', 'bmp', 'webp', *additional_destenations]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = [
        ('webm', MimeUtil.Video.Webm),
        ('ogv', MimeUtil.Video.Ogg),
        ('mp4', MimeUtil.Video.Mp4)
    ]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
    ]

    function = ffmpeg_content_gen.get_video_thumbnail_function
    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


def initialize_ffmpeg_viewable_video_gen(converter: FileConverter):
    source_formats = []  # 'mpv', 'mp4', 'avi', 'wmv', 'mov', *additional_sources]
    dest_formats = []  # 'ogv', 'mp4', *additional_destenations]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = [
        ('webm', MimeUtil.Video.Webm),
        ('ogv', MimeUtil.Video.Ogg),
        ('mp4', MimeUtil.Video.Mp4)
    ]
    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webm', MimeUtil.Video.Webm),
        ('ogv', MimeUtil.Video.Ogg),
        ('mp4', MimeUtil.Video.Mp4)
    ]
    function = ffmpeg_content_gen.get_viewable_function
    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


def initialize_ffmpeg_viewable_audio_gen(converter: FileConverter):
    source_formats = []  # ['webm', 'mpv', 'ogv', 'mp4', 'avi', 'wmv', 'mov', *additional_sources]
    dest_formats = []  # ['ogv', 'mp4', 'webm', *additional_destenations]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = [
        ('webm', MimeUtil.Audio.Webm),
        ('oga', MimeUtil.Audio.Ogg),
        ('mp3', MimeUtil.Audio.Mpeg),
        ('wav', MimeUtil.Audio.Wav)
    ]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webm', MimeUtil.Audio.Webm),
        ('oga', MimeUtil.Audio.Ogg),
        ('mp3', MimeUtil.Audio.Mpeg),
        ('wav', MimeUtil.Audio.Wav)
    ]

    function = ffmpeg_content_gen.get_viewable_function
    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


# LIBRE OFFICE ====================
def initialize_libreoffice_viewable_gen(converter: FileConverter):
    source_formats = ['doc', 'docx', 'odt', 'odp', 'ods', ]
    dest_formats = ['pdf']

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = []

    function = libre_office_content_gen.get_convert_function
    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


def initialize_libreoffice_thumbnail_gen(converter: FileConverter):
    source_formats = ['doc', 'docx', 'odt', 'odp', 'ods', ]
    dest_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
    ]

    def get_func(format: str) -> GeneratorFunction:
        to_img_func = libre_office_content_gen.get_convert_function('png')
        to_thumb_func = pillow_content_gen.get_thumbnail_function(format)
        return pipe_generators(to_img_func, to_thumb_func)

    function = get_func
    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


# POPPLER ====================
def initialize_poppler_thumbnail_gen(converter: FileConverter):
    source_formats = ['pdf', 'ai']  # adobe illustrator is just pdf
    dest_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
    ]

    function = poppler_content_gen.get_thumbnail_function

    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


def initialize_pillow_thumbnail_gen(converter: FileConverter):
    source_formats = ['tif', 'psd', 'xcf']
    dest_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
        ('gif', MimeUtil.Image.Gif),
    ]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
        ('gif', MimeUtil.Image.Gif),
    ]

    function = pillow_content_gen.get_thumbnail_function

    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


# PILLOW ====================
def initialize_pillow_viewable_gen(converter: FileConverter):
    source_formats = ['tif', 'psd', 'xcf']
    dest_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
    ]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('png', MimeUtil.Image.Png),
        ('bmp', MimeUtil.Image.Bmp),
        ('jpg', MimeUtil.Image.Jpeg),
        ('gif', MimeUtil.Image.Gif),
    ]

    function = pillow_content_gen.get_viewable_function

    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


def initialize_pillow_animated_viewable_gen(converter: FileConverter):
    source_formats = []
    dest_formats = []

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_source_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('gif', MimeUtil.Image.Gif),
    ]

    # webm is stupid, in that it could be video or audio, we explicitly state what it is here
    mimed_dest_formats = [
        ('webp', MimeUtil.Image.Webp),
        ('gif', MimeUtil.Image.Gif),
    ]

    # partial wont work cause of positional args?
    # think it should work but i did something wrong
    def wrapper(format: str):
        return pillow_content_gen.get_viewable_function(format, animated=True)

    function = wrapper

    register_helper(converter, function,
                    source_formats=source_formats, dest_formats=dest_formats,
                    source_mimes=mimed_source_formats, dest_mimes=mimed_dest_formats)


# EASY INIT ====================
def initialize_viewable_gen(converter: FileConverter):
    initialize_ffmpeg_viewable_audio_gen(converter)
    initialize_ffmpeg_viewable_video_gen(converter)
    initialize_libreoffice_viewable_gen(converter)
    initialize_pillow_viewable_gen(converter)
    initialize_pillow_animated_viewable_gen(converter)


def initialize_thumbnail_gen(converter: FileConverter):
    initialize_ffmpeg_thumbnail_gen(converter)
    initialize_libreoffice_thumbnail_gen(converter)
    initialize_pillow_thumbnail_gen(converter)
    initialize_poppler_thumbnail_gen(converter)


def initialize_gen(viewable: FileConverter, thumbnail: FileConverter):
    initialize_viewable_gen(viewable)
    initialize_thumbnail_gen(thumbnail)
