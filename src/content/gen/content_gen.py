import enum
from io import BytesIO
from typing import Union, List, Tuple, Callable, Dict, Any
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


def pipe_generators(*functions: GeneratorFunction) -> GeneratorFunction:
    def pipe_function(input: BytesIO, output: BytesIO):
        current_temp = BytesIO()

        # input is used the first time, passing into a temporary pipe stream
        functions[0](input, current_temp)

        # we want to loop from the second to the second to last
        # this range will use a temporary bytesio to pipe the information between generators

        for index in range(1, len(functions) - 1):
            next_temp = BytesIO()
            current_temp.seek(0)
            functions[index](current_temp, next_temp)
            current_temp.close()
            current_temp = next_temp

        # output is used the last time, parsing the pipe stream and then passing into our output
        current_temp.seek(0)
        functions[-1](current_temp, output)
        current_temp.close()

    # perform pipe
    if len(functions) > 1:
        return pipe_function
    # We could check for only one function and return that but instead...
    # We raise an error to avoid confusing expected behaviour, this allows us to catch improper use
    else:
        raise ValueError("Piping requires at least 2 functions!")


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

    def generate(self, source_type: MimeType, req_type: MimeType, file: BytesIO, output: BytesIO) -> bool:
        func = self.get_function(source_type, req_type)
        if func is None:
            return False
        else:
            func(file, output)
            return True

    def get_request_map(self, req_type: MimeType) -> List[MimeType]:
        results = []
        for source, pair in self.map:
            for request, _ in pair:
                if request in req_type:
                    results.append(request)
        return results
