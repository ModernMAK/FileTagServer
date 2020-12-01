from typing import List, Any, Dict

from src import config
from src.database_api.clients import MasterClient
from src.page_groups.page_group import PageGroup, ServeResponse
from src.util.typing import LiteSpeedRequest

FileData = Dict[str, Any]
TagData = Dict[str, Any]


class ApiPageGroup(PageGroup):
    api: MasterClient = None

    @classmethod
    def initialize(cls):
        cls.api = MasterClient(db_path=config.db_path)

    @classmethod
    def add_routes(cls):
        get_only = ['GET']
        pass

        # cls._add_route(
        #     routing.WebRoot.root,
        #     function=cls.index,
        #     methods=get_only)
        #
        # cls._add_route(
        #     routing.FilePage.root,
        #     function=cls.index,
        #     methods=get_only)
        #
        # cls._add_route(
        #     routing.FilePage.index_list,
        #     function=cls.view_as_list,
        #     methods=get_only)
        #
        # cls._add_route(
        #     routing.FilePage.view_file,
        #     function=cls.view_file,
        #     methods=get_only)

    @classmethod
    def get_file_list(cls, request: LiteSpeedRequest) -> ServeResponse:
        raise NotImplementedError


    # Get File / Tag Pairs

    # Get Files only

    # Get Tags only -

    @classmethod
    def get_file_list_internal(cls, page=0, size=0, order_by: str = None, ids: List[int] = None) -> List[Any]:
        file = cls.api.file
        tags = cls.api.tag












        query = file.get_select_query(offset=page * size, limit=size, ids=ids)
        results = f._fetch_all_mapped(query, f._get_mapping())
