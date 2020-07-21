import shutil
from typing import List

from src.util import path_util
import os.path

from src.content.content_gen import AbstractContentGenerator, GeneratedContentType


class RawContentGenerator(AbstractContentGenerator):

    @classmethod
    def get_supported_types(cls) -> List[str]:
        image = cls.get_supported_image_types()
        video = cls.get_supported_image_types()
        audio = cls.get_supported_image_types()
        result = []
        result.extend(image)
        result.extend(video)
        result.extend(audio)
        return result

    @classmethod
    def get_supported_image_types(cls) -> List[str]:
        return ['png', 'jpeg', 'jpg', 'gif', 'svg', 'bmp']

    @classmethod
    def get_supported_music_types(cls) -> List[str]:
        return ['mp3', 'wav', 'ogg']

    @classmethod
    def get_supported_video_types(cls) -> List[str]:
        return ['mp4', 'webm', 'ogv']

    def generate(self, source_path: str, dest_folder: str, **kwargs):
        ext = path_util.get_formatted_ext(source_path)
        local_copy_path = os.path.join(dest_folder, self.get_file_name(GeneratedContentType.LocalCopy, ext))

        if not os.path.exists(local_copy_path) or kwargs.get('rebuild', False):
            shutil.copyfile(source_path, local_copy_path)

    def get_file_name(self, content_type: GeneratedContentType, source_ext: str):
        return f"LocalCopy.{source_ext}"
