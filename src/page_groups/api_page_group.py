from typing import List, Any, Dict, Union, Callable

from src import config
from src.database_api import database_search
from src.database_api.clients import MasterClient, FileTable, FileTagMapTable, TagTable
from src.database_api.clients.file_extra_info import FileExtraInfoTable, FileExtraInfoClient
from src.database_api.database_search import SqliteQueryBuidler
from src.page_groups import routing
from src.page_groups.page_group import PageGroup, ServeResponse
from src.util.collection_util import get_unique_values_on_key
from src.util.db_util import sanitize
from src.util.mytyping import LiteSpeedRequest

FileData = Dict[str, Any]
FileDataList = List[FileData]
TagData = Dict[str, Any]
TagDataList = List[TagData]
ApiResponse = Dict[str,Any]

class ApiError(Exception):
    def __init__(self, message:str):
        self.message = message

class FileApi:
    client: MasterClient = None
    @classmethod
    def initialize(cls):
        cls.client = MasterClient(db_path=config.db_path)

    @staticmethod
    def reformat(files: Union[FileData, FileDataList]):
        display_local_path = True
        display_remote_path = True

        def reformat(data: Dict[Any, Any]):
            # Hide local path from remote users
            if not display_local_path:
                del data[FileTable.path]
            # Hide remote path?
            if display_remote_path:
                partial_url = routing.FilePage.get_serve_file_raw(data['id'])
                data['url'] = routing.full_path(partial_url)

            data['page'] = routing.full_path(routing.FilePage.get_view_file(data['id']))

        if isinstance(files, list):
            for file in files:
                reformat(file)
        else:
            reformat(files)

    @classmethod
    def get_list(cls, page: int = 0, size: int = 50, search: str = None, **kwargs) -> FileDataList:
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

            ids = cls.client._fetch_all_mapped(search_query, [FileTable.id])
            ids = [f['id'] for f in ids]
            files = cls.client.file.fetch(ids=ids)
        else:
            files = cls.client.file.fetch(limit=size, offset=page * size)

        # Files should now be a list of dictionaries

        # So, Grab unique ids
        unique_ids = get_unique_values_on_key(files, FileTable.id)
        # Fetch all rows that match a file
        # This gets a lookup table; file_id -> many tag_ids
        file_tag_lookup = cls.client.map.fetch_lookup_groups(key=FileTagMapTable.file_id, files=unique_ids)
        # This gets a list; which we know is a unique set; hacky but that's what this does
        unique_tags = cls.client.map.fetch_lookup_groups(key=FileTagMapTable.tag_id, files=unique_ids).keys()
        unique_tags = [v for v in unique_tags]
        # Fetch tag lookup from unique_tags
        tag_lookup = cls.client.tag.fetch_lookup(ids=unique_tags)

        # Add Tag Info & Fix url
        TagApi.reformat(tag_lookup.values())

        # Match Tags to files & Fix url
        for file in files:
            # Create new tags field
            tags = []
            file['tags'] = tags
            for map_info in file_tag_lookup.get(file[FileTable.id], []):
                tag_id = map_info[FileTagMapTable.tag_id]
                tags.append(tag_lookup[tag_id])

        cls.reformat(files)
        return files

    @classmethod
    def get_data(cls, ids: List[int], **kwargs) -> FileDataList:
        files = cls.client.file.fetch(ids=ids)
        if len(files) == 0:
            raise NotImplementedError
        file_tag_lookup = cls.client.map.get_file2tag_lookup(file_ids=ids)
        for file in files:
            file_id = file['id']
            tags = file_tag_lookup[file_id]
            file['tags'] = tags

        cls.reformat(files)
        return files

    @classmethod
    def get_search_count(cls, search: str = None, **kwargs) -> int:
        if search is not None:
            search_parts = search.split(" ")
            groups = database_search.create_simple_search_groups(search_parts)
            raw_query = database_search.create_query_from_search_groups(groups)
            return cls.client._count(raw_query)
        else:
            return cls.client.file.count()

class TagApi:
    client: MasterClient = None
    @classmethod
    def initialize(cls):
        cls.client = MasterClient(db_path=config.db_path)

    @staticmethod
    def reformat(tag_list: Union[TagData, List[TagData]]):
        def reformat_tag(tag_data: TagData):
            partial_url = routing.TagPage.get_view_tag(tag_data['id'])
            tag_data['page'] = routing.full_path(partial_url)

        if not isinstance(tag_list, dict):
            for tag in tag_list:
                reformat_tag(tag)
        else:
            reformat_tag(tag_list)

    @classmethod
    def get_list(cls, page: int = 0, size: int = 50, search: str = None, **kwargs) -> List[TagData]:
        page = int(page)
        size = int(size)

        # TODO support search
        tags = cls.client.tag.fetch(limit=size, offset=page * size)

        # Add Tag Info & Fix url
        cls.reformat(tags)
        return tags

    @classmethod
    def get_autocorrect(cls, tag: str, **kwargs):
        query = SqliteQueryBuidler()
        query \
            .Select(TagTable.name_qualified, TagTable.count_qualified) \
            .From(TagTable.table) \
            .Where(f"{TagTable.name_qualified} LIKE '{tag}%'") \
            .OrderBy((TagTable.count_qualified, False))

    @classmethod
    def get_valid_tags(cls, tag_list, invert: bool = False):
        valid_tags = cls.client.tag.fetch(names=tag_list)
        # print(valid_tags)
        if invert:
            missing_tags = {tag: {'name': tag} for tag in tag_list}
            for valid_tag in valid_tags:
                del missing_tags[valid_tag['name']]
            missing_tags = [tag for tag in missing_tags.values()]  # dict to list
            # print(missing_tags)
            for tag in missing_tags:
                tag['id'] = None
                tag['page'] = None
                tag['description'] = None
                tag['count'] = None
            return missing_tags
        else:
            return valid_tags


class Api:
    client: MasterClient = MasterClient(db_path=config.db_path)

    @classmethod
    def obsolete_get_all_duplicate_list(cls):
        query = SqliteQueryBuidler()
        iq = query.Select(FileExtraInfoTable.file_id, "COUNT(*) as duplicates").From(FileExtraInfoTable.table).Raw(
            f"GROUP BY {FileExtraInfoTable.hash_qualified} {FileExtraInfoTable.size_qualified}").flush()

        # "SELECT file_id, duplicates from (SELECT file_id, COUNT(*) AS duplicates FROM file_extra_info GROUP BY hash, size) where duplicates > 1"
        q = query \
            .Select(FileExtraInfoTable.file_id, "duplicates") \
            .From(f"({iq})") \
            .Where("duplicates > 1") \
            .flush()

        r = cls.client._fetch_all_mapped(q, ['file_id', 'count'])
        touched = set()
        dupes = []
        for row in r:
            id = row['file_id']
            if id in touched:
                continue
            f_dupes = cls.get_duplicate_file_list(id, ignore_self=False)
            dupes.append(f_dupes)
            for f_id in f_dupes:
                touched.update(f_id)
        return dupes

    @classmethod
    def get_duplicate_file_list(cls, file_id, ignore_self: bool = True, **kwargs):
        results = cls.client.file_info.fetch(files=[file_id])
        if len(results) == 0:
            return []
        # print(results)
        result = results[0]
        query = SqliteQueryBuidler()

        where_parts = [
            f"{FileExtraInfoTable.hash_qualified} = '{result['hash']}'",
            f"{FileExtraInfoTable.size_qualified} = {result['size']}",
        ]
        if ignore_self:
            where_parts.append(f"{FileExtraInfoTable.file_id_qualified} != {file_id}")

        q = query \
            .Select(FileExtraInfoTable.id_qualified, FileExtraInfoTable.file_id_qualified,
                    FileExtraInfoTable.size_qualified, FileExtraInfoTable.hash_qualified) \
            .From(FileExtraInfoTable.table) \
            .Where(" AND ".join(where_parts)) \
            .flush()
        # print(q)

        ids = cls.client.file_info._fetch_all_mapped(q, FileExtraInfoClient._get_mapping())
        # print(ids)
        ids = [row['file_id'] for row in ids]

        return ids

    @classmethod
    def update_file_info(cls, file_id, name: str = None, description: str = None, tags: List[int] = None,
                         **kwargs) -> None:
        query = SqliteQueryBuidler()
        f_set: List[str] = []

        if name is not None:
            f_set.append(f"{FileTable.name} = {sanitize(name)}")

        if description is not None:
            f_set.append(f"{FileTable.description} = {sanitize(description)}")

        if len(f_set) > 0:
            f_query = query \
                .Update(FileTable.table) \
                .Set(", ".join(f_set)) \
                .Where(f"{FileTable.id} = {file_id}") \
                .flush()
            cls.client._execute(f_query)

        if tags is not None:
            ftm_clear_query = query \
                .Delete().From(FileTagMapTable.table) \
                .Where(f"{FileTagMapTable.file_id} = {file_id}") \
                .flush()

            cls.client._execute(ftm_clear_query)

            # insert missing
            ftm_values = []
            for tag_id in tags:
                v = (file_id, tag_id)
                ftm_values.append(v)

            ftm_query = query.Insert().Or().Ignore() \
                .Into(FileTagMapTable.table) \
                .Columns(FileTagMapTable.file_id, FileTagMapTable.tag_id) \
                .Values(*ftm_values) \
                .flush()
            cls.client._execute(ftm_query)

class ApiPageGroup(PageGroup):
    @classmethod
    def initialize(cls, **kwargs):
        FileApi.initialize()
        TagApi.initialize()

    @classmethod
    def add_routes(cls):
        wildcard = "([A-Za-z0-9]*)"
        cls._add_route(routing.ApiPage.get_file_data(wildcard), cls.get_file_data, methods=['GET'])
        cls._add_route(routing.ApiPage.get_file_list(wildcard), cls.get_file_list, methods=['GET'])
        cls._add_route(routing.ApiPage.get_tag_list(wildcard), cls.get_tag_list, methods=['GET'])
        cls._add_route(routing.ApiPage.get_tag_autocorrect(wildcard), cls.get_tag_autocorrect, methods=['GET'])

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
    def get_file_data(cls, request: Dict, format: str):
        cls.serve_api_request(request, format, FileApi.get_data)

    @classmethod
    def get_file_list(cls, request: Dict, format: str):
        cls.serve_api_request(request, format, FileApi.get_list)

    # @classmethod
    # def get_file_search_count(cls, request: LiteSpeedRequest, format: str) -> Union[ServeResponse, Dict[Any, Any]]:
    #     return cls.serve_api_request(request, format, Api.get_search_count)

    @classmethod
    def get_tag_list(cls, request: LiteSpeedRequest, format: str) -> Union[ServeResponse, Dict[Any, Any]]:
        return cls.serve_api_request(request, format, TagApi.get_list)

    @classmethod
    def get_tag_autocorrect(cls, request: LiteSpeedRequest, format:str):
        return cls.serve_api_request(request, "json", TagApi.get_autocorrect)


