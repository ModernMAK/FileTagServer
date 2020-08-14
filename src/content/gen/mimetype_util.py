from enum import Enum


# I get it, not having it in a class means its easy to expand upon
# but why can i not find an easy way of asking for a mimetype without having a file


class MimeUtil:
    class Application:

        @classmethod
        def get_name(cls, name: str):
            return f"application/{name}"

        @classmethod
        def get_mime(cls, name: str, enc: str = None):
            return cls.get_name(name), enc

        Javascript = get_mime('javascript')
        Json = get_mime('json')
        Ms_Word = get_mime('msword')
        Octet_Stream = get_mime('octet-stream')
        Oda = get_mime('oda')
        Pdf = get_mime('pdf')

    class Video:

        @classmethod
        def get_name(cls, name: str):
            return f"video/{name}"

        @classmethod
        def get_mime(cls, name: str, enc: str = None):
            return cls.get_name(name), enc

        Webm = get_mime('webm')
        Ogg = get_mime('ogg')
        Mp4 = get_mime('mp4')

    class Audio:
        @classmethod
        def get_name(cls, name: str):
            return f"audio/{name}"

        @classmethod
        def get_mime(cls, name: str, enc: str = None):
            return cls.get_name(name), enc

        Wav = get_mime('wav')
        Mpeg = get_mime('mpeg')
        Mp4 = get_mime('mp4')
        Aac = get_mime('aac')
        Aacp = get_mime('aacp')
        Ogg = get_mime('ogg')
        Webm = get_mime('webm')
        Flac = get_mime('flac')

    class Image:
        @classmethod
        def get_name(cls, name: str):
            return f"image/{name}"

        @classmethod
        def get_mime(cls, name: str, enc: str = None):
            return cls.get_name(name), enc

        Png = get_mime('png')
        Bmp = get_mime('bmp')
        Tiff = get_mime('tiff')
        Jpeg = get_mime('jpeg')
        Webp = get_mime('webp')
        Gif = get_mime('gif')
