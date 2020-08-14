import mimetypes
from typing import Any, Tuple, Dict, Union
from litespeed import route, serve

from src.content.gen.content_gen import StaticContentType
from src.content.management.content_management import ContentManager, ContentFilePathResolver
from src.routing.pages.page_group import PageGroup


class GeneratedContentGroup(PageGroup):
    @classmethod
    def add_routes(cls):
        route(cls.get_file_path("(\d*)"),
              function=cls.as_route_func(cls.serve_file),
              no_end_slash=True,
              methods=['GET'])

        raise NotImplementedError

    manager = None # ContentManager()
    resolver = None # ContentFilePathResolver()

    @classmethod
    def initialize(cls, **kwargs):
        cls.manager = kwargs.get('content_manager')
        cls.resolver = cls.manager.file_path_resolver

    @classmethod
    def get_file_content_context(cls, file_id: int, content_type: StaticContentType) -> Dict[str, Any]:
        if content_type == StaticContentType.Raw:
            real_path = cls.resolver.get_source_file_path(file_id)
            source_mime = cls.manager.generator._get_source_mime(file_id)
            web_path = cls.get_file_source_path(file_id)
            mime_format = source_mime.split(",")[0]
        else:
            if content_type == StaticContentType.Viewable:
                real_paths = cls.manager.get_viewable_paths(file_id)
                web_path = cls.get_file_viewable_path(file_id)
            elif content_type == StaticContentType.Thumbnail:
                real_paths = cls.manager.get_thumbnail_paths(file_id)
                web_path = cls.get_file_thumbnail_path(file_id)
            else:
                raise NotImplementedError

            if len(real_paths) > 0:
                real_path = real_paths[0]
                mime_format, _ = mimetypes.guess_type(real_path)
            else:
                real_path = None
                mime_format = "/"

        format = mime_format.split("/")
        format_group, sub_format = format[0], format[1]

        if real_path is None:
            return {'unsupported': {}}

        embed_formats = ['application/pdf']

        if format_group == 'image':
            return {'image': {'source': web_path}}
        elif format_group == 'video':
            return {'video': {'source': web_path, 'type': sub_format}}
        elif format_group == 'audio':
            return {'audio': {'source': web_path, 'type': sub_format}}
        elif format in embed_formats:
            return {'embed': {'source': web_path, 'type': format}}
        else:
            return {'unsupported': {}}

    @classmethod
    def _serve(cls, request: Dict[str, Any], path: str):
        return serve(path, range=request.get('range'))

    @classmethod
    def serve_file(cls, request: Dict[str, Any], file_id: int):
        get_args = request['GET']
        src = get_args['source']
        # fmt = get_args.get('format', None)

        src_map = {
            'raw': StaticContentType.Raw,
            'viewable': StaticContentType.Viewable,
            'thumbnail': StaticContentType.Thumbnail,
        }
        content_type = src_map[src]
        if content_type == StaticContentType.Raw:
            path = cls.resolver.get_source_file_path(file_id)
        elif content_type == StaticContentType.Thumbnail:
            path = cls.manager.get_thumbnail_paths(file_id)
        elif content_type == StaticContentType.Viewable:
            path = cls.manager.get_viewable_paths(file_id)
        else:
            raise NotImplementedError
        return cls._serve(request, path)

    @classmethod
    def get_file_path(cls, file_id: Union[str, int], get_args: str = None):
        if get_args:
            get_args = ""

        return f"/file/{file_id}{get_args}"

    @classmethod
    def get_file_source_path(cls, file_id: Union[str, int]):
        get_str = cls.to_get_string(
            source="raw"
        )
        return cls.get_file_path(file_id, get_str)

    @classmethod
    def get_file_thumbnail_path(cls, file_id: Union[str, int]):  # , format: str):
        get_str = cls.to_get_string(
            source="thumbnail",
            # format=format
        )
        return cls.get_file_path(file_id, get_str)

    @classmethod
    def get_file_viewable_path(cls, file_id: Union[str, int]):  # , format: str):
        get_str = cls.to_get_string(
            source="viewable",
            # format=format
        )
        return cls.get_file_path(file_id, get_str)
