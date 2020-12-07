from typing import List, Any, Dict, Union, Callable

from src import config
from src.database_api import database_search
from src.database_api.clients import MasterClient, FileTable, FileTagMapTable, TagTable
from src.database_api.database_search import SqliteQueryBuidler
from src.page_groups import routing
from src.page_groups.page_group import PageGroup, ServeResponse
from src.util.collection_util import get_unique_values_on_key
from src.util.mytyping import LiteSpeedRequest

FileData = Dict[str, Any]
TagData = Dict[str, Any]



class ApiPageGroup(PageGroup):
    api: MasterClient = None

    @classmethod
    def initialize(cls):
        cls.api = MasterClient(db_path=config.db_path)

    @classmethod
    def add_routes(cls):
        cls._add_route(routing.ApiPage.get_file_list("([A-Za-z0-9]*)"), cls.get_file_list, methods=['GET'])

    @classmethod
    def serve_api_result(cls, result: Dict[Any, Any], format: str) -> Union[ServeResponse, Dict[Any, Any]]:
        format = format.lower()
        allowed_formats = ['json']  # we only support json right now (Litespeed does natively)
        if format in allowed_formats:
            return result

    @classmethod
    def serve_api_request(cls, request: LiteSpeedRequest, format: str,
                          func: Callable) -> Union[ServeResponse, Dict[Any, Any]]:
        results = func(**request['GET'])
        results = {'result': results}
        return cls.serve_api_result(results, format)

    @classmethod
    def reformat_tag_info(cls, tag_list: Union[Dict[Any, Any], List[Dict[Any, Any]]]):
        def reformat(tag: Dict[Any, Any]):
            partial_url = routing.TagPage.get_view_tag(tag['id'])
            tag['page'] = routing.full_path(partial_url)

        if not isinstance(tag_list, dict):
            for tag in tag_list:
                reformat(tag)
        else:
            reformat(tag_list)

    @classmethod
    def reformat_file_info(cls, tag_list: Union[Dict[Any, Any], List[Dict[Any, Any]]]):
        display_local_path = True
        display_remote_path = True

        def reformat(file: Dict[Any, Any]):
            # Cleanup 'path' field if we are hiding it
            # (this would reveal the file path of the user, among other things)
            # This is okay for personal use, but would be bad in most other situations
            if not display_local_path:
                del file[FileTable.path]

            # this should be a url to the asset
            if display_remote_path:
                partial_url = routing.FilePage.get_serve_file_raw(file['id'])
                file['url'] = routing.full_path(partial_url)

            # a link to the page for this post
            file['page'] = routing.full_path(routing.FilePage.get_view_file(file['id']))

        if isinstance(tag_list, list):
            for tag in tag_list:
                reformat(tag)
        else:
            reformat(tag_list)

    @classmethod
    def get_file_list(cls, request: LiteSpeedRequest, format: str) -> Union[ServeResponse, Dict[Any, Any]]:
        return cls.serve_api_request(request, format, cls.get_file_list_internal)

    @classmethod
    def get_file_list_internal(cls, page: int = 0, size: int = 50, search: str = None, **kwargs) -> \
            List[Dict[str, Any]]:
        # TODO ask falcon to maybe impliment a LiteSpeed StatusCodeError
        # TODO (cont) which will automatically be caught by litespeed and be interpreted as the appropriate error code
        # TODO (cont) it could still be caught by python and nested?

        # this would have been really helpful to raise 404 for invalid pages
        # but i decided the api should just return an empty list instead, as 404 implies that the url is invalid
        # still, the above is a great idea

        page = int(page)
        size = int(size)
        if search is not None:
            search = str(search)

        query = SqliteQueryBuidler()
        if search is not None:
            search_parts = search.split(" ")
            groups = database_search.create_simple_search_groups(search_parts)
            raw_query = database_search.create_query_from_search_groups(groups)
            search_query = query \
                .Raw(raw_query) \
                .Limit(size) \
                .Offset(page * size) \
                .flush()

            ids = cls.api._fetch_all_mapped(search_query, [FileTable.id])
            files = cls.api.file.fetch(ids=ids)
        else:
            files = cls.api.file.fetch(limit=size, offset=page * size)

        # Files should now be a list of dictionaries

        # So, Grab unique ids
        unique_ids = get_unique_values_on_key(files, FileTable.id)
        # Fetch all rows that match a file
        # This gets a lookup table; file_id -> many tag_ids
        file_tag_lookup = cls.api.map.fetch_lookup_groups(key=FileTagMapTable.file_id, files=unique_ids)
        # This gets a list; which we know is a unique set; hacky but that's what this does
        unique_tags = cls.api.map.fetch_lookup_groups(key=FileTagMapTable.tag_id, files=unique_ids).keys()
        # Fetch tag lookup from unique_tags
        tag_lookup = cls.api.tag.fetch_lookup(ids=unique_tags)

        # Add Tag Info & Fix url
        cls.reformat_tag_info(tag_lookup.values())

        # Match Tags to files & Fix url
        for file in files:
            # Create new tags field
            tags = []
            file['tags'] = tags
            for map_info in file_tag_lookup.get(file[FileTable.id], []):
                tag_id = map_info[FileTagMapTable.tag_id]
                tags.append(tag_lookup[tag_id])

        cls.reformat_file_info(files)

        return files

    @classmethod
    def get_file(cls, request: Dict, format: str):
        cls.serve_api_request(request, format, cls.get_file_internal)

    @classmethod
    def get_file_internal(cls, id: int, **kwargs):

        results = cls.api.file.fetch(ids=[id])

        if len(results) == 0:
            raise NotImplementedError

        file = results[0]

        # Files should now be a list of dictionaries
        # This gets a list; which we know is a unique set; hacky but that's what this does
        unique_tags = cls.api.map.fetch_lookup_groups(key=FileTagMapTable.tag_id, files=[id]).keys()
        # Fetch tag lookup from unique_tags
        tags = cls.api.tag.fetch(ids=unique_tags)

        # Add Tag Info & Fix url
        cls.reformat_tag_info(tags)

        # Add Tag Info & Fix url
        # Create new tags field
        file['tags'] = tags

        cls.reformat_file_info(file)

        return file

    @classmethod
    def get_file_count(cls, request: LiteSpeedRequest, format: str) -> Union[ServeResponse, Dict[Any, Any]]:
        return cls.serve_api_request(request, format, cls.get_file_count_internal)

    @classmethod
    def get_file_count_internal(cls, search: str = None, **kwargs) -> int:
        if search is not None:
            search_parts = search.split(" ")
            groups = database_search.create_simple_search_groups(search_parts)
            raw_query = database_search.create_query_from_search_groups(groups)
            return cls.api._count(raw_query)
        else:
            return cls.api.file.count()

    @classmethod
    def get_tag_list(cls, request: LiteSpeedRequest, format: str) -> Union[ServeResponse, Dict[Any, Any]]:
        return cls.serve_api_request(request, format, cls.get_tag_list_internal)

    @classmethod
    def get_tag_list_internal(cls, page: int = 0, size: int = 50, search: str = None, **kwargs) -> List[Dict[str, Any]]:
        page = int(page)
        size = int(size)

        # TODO support search
        tags = cls.api.tag.fetch(limit=size, offset=page * size)

        # Add Tag Info & Fix url
        cls.reformat_tag_info(tags)
        return tags

    @classmethod
    def get_tag_autocorrect(cls, request: LiteSpeedRequest):
        return cls.serve_api_request(request, "json", cls.get_tag_autocorrect_internal)

    @classmethod
    def get_tag_autocorrect_internal(cls, tag: str, **kwargs):
        query = SqliteQueryBuidler()
        query \
            .Select(TagTable.name_qualified, TagTable.count_qualified) \
            .From(TagTable.table) \
            .Where(f"{TagTable.name_qualified} LIKE '{tag}%'") \
            .OrderBy((TagTable.count_qualified, False))
