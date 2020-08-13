import enum
from io import BytesIO
from typing import Union, List, Tuple, Callable, Dict
from src.util import path_util


class GeneratedContentType(enum.Enum):
    Thumbnail = 1  # Image
    Viewable = 2  # Original-Like File


class StaticContentType(enum.Enum):
    Raw = 0
    Thumbnail = 1
    Viewable = 2


MimeType = Tuple[str, str]
GeneratorFunction = Callable[[BytesIO, BytesIO], None]
RegisterFuncType = Callable[[MimeType, MimeType, GeneratorFunction], None]


class FileConverter:
    def __init__(self):
        self.map = {}

    def get_source_map(self, source_type: MimeType) -> Union[Dict[MimeType, GeneratorFunction], None]:
        return self.map.get(source_type, None)

    def get_function(self, source_type: MimeType, req_type: MimeType) -> Union[GeneratorFunction, None]:
        source_map = self.map.get(source_type, None)
        if source_map is None:
            return None
        return source_map.get(req_type, None)

    def register(self, source_type: MimeType, req_type: MimeType, function: GeneratorFunction):
        source_map = self.get_source_map(source_type)
        if source_map is None:
            self.map[source_type] = {req_type: function}
        else:
            source_map[req_type] = function

    def generate(self, source_type: MimeType, req_type: MimeType, file: BytesIO, output: BytesIO) -> None:
        func = self.get_function(source_type, req_type)
        if func is None:
            raise NotImplementedError
        else:
            func(file, output)

    def get_request_map(self, req_type: MimeType) -> List[MimeType]:
        results = []
        for source, pair in self.map:
            for request, _ in pair:
                if request in req_type:
                    results.append(request)
        return results

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


class SimpleContentGenerator:
    def _generate_thumbnail(self, file: BytesIO, file_type: str) -> Union[Tuple[bytes, str], None]:
        raise NotImplementedError

    def _generate_viewable(self, file: BytesIO, file_type: str) -> Union[Tuple[bytes, str], None]:
        raise NotImplementedError

    def generate(self, file: BytesIO, file_type: str, content: GeneratedContentType) -> Union[Tuple[bytes, str], None]:
        if content == GeneratedContentType.Thumbnail:
            return self._generate_thumbnail(file, file_type)
        elif content == GeneratedContentType.Viewable:
            return self._generate_thumbnail(file, file_type)
        else:
            raise ValueError(content + " is not supported!")


class ContentGenerationManager:
    generators = {}

    @classmethod
    def register_generator(cls,
                           extension: Union[List[str], Tuple[str], str],
                           generator: SimpleContentGenerator,
                           allow_override: bool = True):
        if isinstance(extension, str):
            extension = [extension]

        for ext in extension:
            if ext not in cls.generators or allow_override:
                cls.generators[ext] = generator

    @classmethod
    def get_generator(cls, file_type: str) -> Union[SimpleContentGenerator, None]:
        return cls.generators.get(file_type, None)


class ContentManager:
    def get_content_local_path(self, file_id: int, content_type: StaticContentType) -> Union[str, None]:
        if content_type == StaticContentType.Raw:
            # TODO File Client to get path
            return

    def generate_content(self, file_id: int, content_type: StaticContentType):


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
