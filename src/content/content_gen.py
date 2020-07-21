import enum
from io import BytesIO
from os.path import exists
from typing import Union, List, Tuple
from src.util import path_util


class GeneratedContentType(enum.Enum):
    Thumbnail = 1  # Image
    Viewable = 2  # Original-Like File

    LocalCopy = -1  # Original File # DEPRICATED, not a 'generated' file


# Content Request
#   range: (start, stop) if None assumes the start and end of the file


class DynamicContentGenerator:
    # Given a file, handle the request
    # Because we expect to do file conversion, if we can batch requests like this, it would be better
    def generate(self, file: BytesIO, **kwargs) -> List[bytes]:
        # Return whole file
        ranges = kwargs.get('ranges')
        if ranges is None:
            return [file.read()]

        # Return partial files
        requests = []
        for range in ranges:
            start, end = range
            if start is None:
                start = 0
            if end is None:
                end = len(file.getbuffer())
            file.seek(start)
            partial = file.read(end - start)
            requests.append(partial)
        return requests


class StaticContentGenerator(DynamicContentGenerator):
    def generate_cache(self, file: BytesIO, cache_path: str, file_ext: str, **kwargs):
        content_types = kwargs.get('content_types')
        if content_types is None:
            content_types = [c for c in GeneratedContentType]

        for content_type in content_types:
            path = self.get_path(cache_path, content_types, file_ext)
            if path is None:
                continue
            if not exists(path) or kwargs.get('regenerate', False):
                with open(path, 'wb') as file:
                    output = self._generate_cache(file, content_type, file_ext, **kwargs)
                    file.write(output)

    def _generate_cache(self, file: BytesIO, content_type: GeneratedContentType, file_ext: str, **kwargs) -> bytes:
        raise NotImplementedError

    def get_bytes(self, cache_path: str, content_type: GeneratedContentType, file_ext: str, **kwargs) -> List[bytes]:
        path = self.get_path(cache_path, content_type, file_ext)
        with open(path, 'rb') as file:
            return super().generate(file, **kwargs)

    def get_path(self, cache_path: str, content_type: GeneratedContentType, file_ext: str):
        raise NotImplementedError


class AbstractContentGenerator:
    def generate(self, source_path: str, dest_folder: str, **kwargs):
        raise NotImplementedError

    def get_file_name(self, content_type: GeneratedContentType, source_ext: str):
        raise NotImplementedError


class ContentGeneration:
    generators = {}

    @classmethod
    def register_generator(cls, extension: Union[List[str], Tuple[str], str], generator: AbstractContentGenerator,
                           allow_override: bool = True):
        if isinstance(extension, str):
            if extension not in generator or allow_override:
                cls.generators[extension] = generator
        else:
            # cls.generators.update({ext: generator for ext in extension})
            for ext in extension:
                if ext not in cls.generators or allow_override:
                    cls.generators[ext] = generator

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
