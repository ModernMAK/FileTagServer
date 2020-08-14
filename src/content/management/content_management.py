import mimetypes
from os.path import join, dirname, exists
from os import makedirs
from typing import List

from src.content.gen.content_gen import StaticContentType, MimeType, FileConverter, GeneratedContentType
from src.content.gen.mimetype_util import MimeUtil
from src.database.clients import FileClient, GeneratedContentClient
from src.util import path_util


class ContentFilePathResolver:
    def __init__(self, db_path: str, cache_folder=None, temp_cache_folder=None):
        if cache_folder is None:
            cache_folder = join(path_util.project_root(), "generated", "cache")

        if temp_cache_folder is None:
            temp_cache_folder = join(path_util.project_root(), "generated", "temporary")

        self.cache_folder = cache_folder
        self.temp_cache_folder = temp_cache_folder
        self.content_client = GeneratedContentClient(db_path=db_path)
        self.file_client = FileClient(db_path=db_path)

    def get_source_file_path(self, file_id: int) -> str:
        results = self.file_client.fetch(ids=[file_id])
        if len(results) == 1:
            return results[0]['path']

        raise NotImplementedError

    def __fetch_content_id(self, file_id: int) -> str:
        results = self.content_client.fetch(file_ids=[file_id])
        if len(results) == 1:
            return results[0]['id']
        raise NotImplementedError

    def get_cache_directory(self, file_id: int) -> str:
        cache_id = str(self.__fetch_content_id(file_id))
        return join(self.cache_folder, cache_id)

    def get_cache_file_path(self, file_id: int, file) -> str:
        directory = self.get_cache_directory(file_id)
        return join(directory, file)

    def get_temp_cache_directory(self, file_id: int) -> str:
        cache_id = str(self.__fetch_content_id(file_id))
        return join(self.temp_cache_folder, cache_id)

    def get_temp_cache_file_path(self, file_id: int, file: str) -> str:
        directory = self.get_temp_cache_directory(file_id)
        return join(directory, file)

    def get_file_path(self, file_id: int, content_type: StaticContentType, requested_ext: str = None) -> str:
        if content_type == StaticContentType.Raw:
            return self.get_source_file_path(file_id)
        elif content_type == StaticContentType.Viewable:
            return join(self.get_temp_cache_directory(file_id), f"Viewable.{requested_ext}")
        elif content_type == StaticContentType.Thumbnail:
            return join(self.get_cache_directory(file_id), f"Thumbnail.{requested_ext}")

        raise NotImplementedError

    def get_file_dir(self, file_id: int, content_type: GeneratedContentType):
        if content_type == GeneratedContentType.Viewable:
            return self.get_temp_cache_directory(file_id)
        elif content_type == GeneratedContentType.Thumbnail:
            return self.get_cache_directory(file_id)
        else:
            raise NotImplementedError


class ContentGenerator:
    def __init__(self, file_path_resolver: ContentFilePathResolver, viewable_gen: FileConverter,
                 thumbnail_gen: FileConverter):
        self.file_path_resolver = file_path_resolver
        self.viewable_gen = viewable_gen
        self.thumbnail_gen = thumbnail_gen

    def _get_source_mime(self, file_id: int):
        results = self.file_path_resolver.file_client.fetch(ids=[file_id])
        if len(results) == 1:
            return results[0]['mime']
        raise NotImplementedError

    def generate_first_viewable(self, file_id: int, dest_mime: List[MimeType]) -> bool:
        for mime in dest_mime:
            if self.generate_viewable(file_id, mime):
                return True
        return False

    def generate_many_viewable(self, file_id: int, dest_mime: List[MimeType]) -> List[bool]:
        return [self.generate_viewable(file_id, mime) for mime in dest_mime]

    def generate_viewable(self, file_id: int, dest_mime: MimeType) -> bool:
        requested_ext = mimetypes.guess_extension(dest_mime)
        source_mime = self._get_source_mime(file_id)
        source_path = self.file_path_resolver.get_file_path(file_id, StaticContentType.Raw)
        dest_path = self.file_path_resolver.get_file_path(file_id, StaticContentType.Viewable, requested_ext)
        return self.__generate_content(self.viewable_gen, source_path, dest_path, source_mime, dest_mime)

    def generate_first_thumbnail(self, file_id: int, dest_mime: List[MimeType]) -> bool:
        for mime in dest_mime:
            if self.generate_thumbnail(file_id, mime):
                return True
        return False

    def generate_many_thumbnail(self, file_id: int, dest_mime: List[MimeType]) -> List[bool]:
        return [self.generate_thumbnail(file_id, mime) for mime in dest_mime]

    def generate_thumbnail(self, file_id: int, dest_mime: MimeType) -> bool:
        requested_ext = mimetypes.guess_extension(dest_mime)
        source_mime = self._get_source_mime(file_id)
        source_path = self.file_path_resolver.get_file_path(file_id, StaticContentType.Raw)
        dest_path = self.file_path_resolver.get_file_path(file_id, StaticContentType.Thumbnail, requested_ext)
        return self.__generate_content(self.thumbnail_gen, source_path, dest_path, source_mime, dest_mime)

    def __generate_content(self, generator: FileConverter, source_path: str, save_path: str, source_mime: MimeType,
                           dest_mime: MimeType) -> bool:
        function = generator.get_function(source_mime, dest_mime)
        if function is None:
            return False

        # make sure directory exists
        makedirs(dirname(save_path))

        with open(source_path, 'rb') as input:
            with open(save_path, 'wb') as output:
                function(input, output)


class ContentManager:
    def __init__(self, generator: ContentGenerator):
        self.generator = generator
        self.file_path_resolver = self.generator.file_path_resolver

    def generate_thumbnails(self, file_id: int) -> bool:
        # Generate 3 thumbnails for browser support;
        # webp for most chromium based browsers, gif (to allow animation), and jpeg (practically universal)
        thumb_mimes = [MimeUtil.Image.Webp, MimeUtil.Image.Gif, MimeUtil.Image.Jpeg]

        return self.generator.generate_first_thumbnail(file_id, thumb_mimes)

    def generate_viewable_image(self, file_id: int) -> bool:
        # Generate 3 thumbnails for browser support;
        # webm for most chromium based browsers, mp4 (practically universal)
        image_mimes = [MimeUtil.Image.Webp, MimeUtil.Image.Gif, MimeType.Image.Png, MimeUtil.Image.Jpeg]
        return self.generator.generate_first_viewable(file_id, image_mimes)

    def generate_viewable_video(self, file_id: int) -> bool:
        # Generate 3 thumbnails for browser support;
        # webm for most chromium based browsers, mp4 (practically universal)
        video_mimes = [MimeUtil.Video.Webm, MimeUtil.Video.Mp4]

        return self.generator.generate_first_viewable(file_id, video_mimes)

    def generate_viewable_audio(self, file_id: int) -> bool:
        # Generate 3 thumbnails for browser support;
        # ogg for most chromium based browsers, mp3 (practically universal)
        audio_mimes = [MimeUtil.Audio.Ogg, MimeUtil.Audio.Mpeg]
        return self.generator.generate_first_viewable(file_id, audio_mimes)

    def generate_viewable_embed(self, file_id: int) -> bool:
        embed_mimes = [MimeUtil.Application.Pdf]
        return self.generator.generate_first_viewable(file_id, embed_mimes)

    def generate_viewable_any(self, file_id: int) -> bool:
        if self.generate_viewable_image(file_id):
            return True
        if self.generate_viewable_audio(file_id):
            return True
        if self.generate_viewable_video(file_id):
            return True
        if self.generate_viewable_embed(file_id):
            return True
        return False

    def get_thumbnail_paths(self, file_id: int) -> List[str]:
        thumb_mimes = [MimeUtil.Image.Webp, MimeUtil.Image.Gif, MimeUtil.Image.Jpeg]
        paths = []
        for mime in thumb_mimes:
            ext = mimetypes.guess_extension(mime)
            path = self.file_path_resolver.get_file_path(file_id, StaticContentType.Thumbnail, ext)
            if not exists(path):
                continue
            paths.append(path)
        return paths

    def get_viewable_paths(self, file_id: int) -> List[str]:
        image_mimes = [MimeUtil.Image.Webp, MimeUtil.Image.Gif, MimeType.Image.Png, MimeUtil.Image.Jpeg]
        video_mimes = [MimeUtil.Video.Webm, MimeUtil.Video.Mp4]
        audio_mimes = [MimeUtil.Audio.Ogg, MimeUtil.Audio.Mpeg]
        embed_mimes = [MimeUtil.Application.Pdf]
        view_mimes = [*image_mimes, *video_mimes, *audio_mimes, *embed_mimes]

        paths = []
        for mime in view_mimes:
            ext = mimetypes.guess_extension(mime)
            path = self.file_path_resolver.get_file_path(file_id, StaticContentType.Viewable, ext)
            if not exists(path):
                continue
            paths.append(path)
        return paths
