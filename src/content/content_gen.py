import enum
from typing import Union, List, Tuple
from src.util import path_util


class GeneratedContentType(enum.Enum):
    Thumbnail = 1  # Image
    Viewable = 2  # Original-Like File
    LocalCopy = 3  # Original File


class AbstractContentGenerator:
    def generate(self, source_path: str, dest_folder: str, **kwargs):
        raise NotImplementedError

    def get_file_name(self, content_type: GeneratedContentType, source_ext: str):
        raise NotImplementedError


class ContentGeneration:
    generators = {}

    @classmethod
    def register_generator(cls, extension: Union[List[str], Tuple[str], str], generator: AbstractContentGenerator):
        if isinstance(extension, str):
            cls.generators[extension] = generator
        else:
            cls.generators.update({ext: generator for ext in extension})

    @classmethod
    def generate(cls, source_path: str, dest_folder: str, **kwargs) -> bool:
        ext = path_util.get_formatted_ext(source_path)
        gen = cls.generators.get(ext)
        if gen is None:
            return False
        else:
            path_util.enforce_dirs_exists(dest_folder)
            gen.generate(source_path, dest_folder, **kwargs)
            return True

    @classmethod
    def get_file_name(cls, content_type: GeneratedContentType, source_ext: str) -> Union[None, str]:
        gen = cls.generators.get(source_ext)
        if gen is None:
            return None
        else:
            return gen.get_file_name(content_type, source_ext)
