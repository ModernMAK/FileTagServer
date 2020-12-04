from typing import List, Any, Dict, Union

from src import config
from src.database_api import database_search
from src.database_api.clients import MasterClient, FileTable, FileTagMapTable
from src.database_api.database_search import SqliteQueryBuidler
from src.page_groups import routing
from src.page_groups.page_group import PageGroup, ServeResponse
from src.util.collection_util import get_unique_values_on_key
from src.util.typing import LiteSpeedRequest

FileData = Dict[str, Any]
TagData = Dict[str, Any]


class PaginationUtil:
    @staticmethod
    def is_page_offset_valid(offset: int, size: int, count: int):
        return count - (offset + size) > 0

    @staticmethod
    def is_page_valid(page: int, size: int, count: int):
        return PaginationUtil.is_page_offset_valid(page * size, size, count)


class ApiPageGroup(PageGroup):
    api: MasterClient = None

    @classmethod
    def initialize(cls):
        cls.api = MasterClient(db_path=config.db_path)

    @classmethod
    def add_routes(cls):
        cls._add_route(routing.ApiPage.get_file_list("([A-Za-z0-9]*)"), cls.get_file_list, methods=['GET'])

    @classmethod
    def get_file_list(cls, request: LiteSpeedRequest, format: str) -> Union[ServeResponse, Dict[Any, Any]]:
        results = cls.get_file_list_internal(**request['GET'])
        results = {'files': results}
        format = format.lower()
        allowed_formats = ['json']

        if format in allowed_formats:
            return results

    @classmethod
    def get_file_list_internal(cls, page: int = 0, size: int = 50, search: str = None, **kwargs) -> \
            List[Dict[str, Any]]:
        # TODO ask falcon to maybe impliment a LiteSpeed StatusCodeError
        # TODO (cont) which will automatically be caught by litespeed and be interpreted as the appropriate error code
        # TODO (cont) it could still be caught by python and nested?

        # this would have been really helpful to raise 404 for invalid pages
        # but i decided the api should just return an empty list instead, as 404 implies that the url is invalid
        # still, the above is a great idea

        display_local_path = True
        display_remote_path = True

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
        # This gets a list; which we know is a unique set
        unique_tags = cls.api.map.fetch_lookup_groups(key=FileTagMapTable.tag_id, files=unique_ids).keys()
        # Fetch tag lookup from unique_tags
        tag_lookup = cls.api.tag.fetch_lookup(ids=unique_tags)

        # Add Tag Info
        for file in files:
            # Create new tags field
            tags = []
            file['tags'] = tags
            for map_info in file_tag_lookup[file[FileTable.id]]:
                tag_id = map_info[FileTagMapTable.tag_id]
                tags.append(tag_lookup[tag_id])

            # Cleanup 'path' field if we are hiding it
            # (this would reveal the file path of the user, among other things)
            # This is okay for personal use, but would be bad in most other situations
            if not display_local_path:
                del file[FileTable.path]

            # this should be a url to the asset
            if display_remote_path:
                file['url'] = routing.FilePage.get_serve_file_raw(file['id'])

        return files
