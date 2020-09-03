from math import ceil
from typing import Dict, Any, List

from src.page_groups import status
from litespeed import serve, route
from pystache import Renderer

from src import config
import src.database_api.clients as dbapi
from src.page_groups import pathing, routing
from src.page_groups.status import serve_error
from src.util.page_utils import reformat_serve
from src.page_groups.page_group import PageGroup, ServeResponse


class TagPageGroup(PageGroup):
    renderer = None

    @classmethod
    def get_navbar_context(cls) -> List[Dict[str, Any]]:
        def helper(link: str, text: str, status: str = None) -> Dict[str, Any]:
            info = {'path': link, 'text': text}
            if status is not None:
                info['status'] = status
            return info

        return [
            helper(FilePage.root, "File"),
            helper(TagPage.root, "Tag", "active")
        ]

    @classmethod
    def add_routes(cls):

        route(routing.TagPage.root,
              function=cls.as_route_func(cls.index),
              no_end_slash=True,
              methods=['GET'])

        route(routing.TagPage.index_list,
              function=cls.as_route_func(cls.view_as_list),
              no_end_slash=True,
              methods=['GET'])

        route(routing.TagPage.view_tag,
              function=cls.as_route_func(cls.view_tag),
              no_end_slash=True,
              methods=['GET'])

    @classmethod
    def initialize(cls, **kwargs):
        cls.renderer = Renderer(search_dirs=[config.template_path])

    @classmethod
    def get_navbar_context(cls):
        return {'tag': 'active'}

    #########
    # Displays the primary page of the tag page group
    # This should almost always either be;
    #   A splash-screen main page for the group
    #   A homepage for the topics of the group
    #   An alias for primary page of the group (deferring to that page display)
    #########
    @classmethod
    def index(cls, request: Dict[str, Any]) -> ServeResponse:
        return status.error_307(request, location=routing.TagPage.index_list)
        # return cls.view_as_list(request)

    #########
    # Displays the tags in the tag database as a list
    # This is primarily intended to be used to edit multiple tags at once
    # GET SUPPORT:
    #   Pagination ~ Page # Only => 'page'
    #       page counts from 1; to reflect the UI
    #########
    @classmethod
    def view_as_list(cls, request: Dict[str, Any]) -> ServeResponse:
        page = int(request.get('GET').get('page', 1))
        client = dbapi.MasterClient(db_path=config.db_path)
        page_size = 50
        search_args = {}
        # Count tags
        # tag_count = client.tag.count(**search_args)
        # Determine if page is valid
        # if not cls.is_page_valid(page, page_size, tag_count) and page != 1:
        #     return serve_error(404)

        # Fetch results for page
        tags = client.tag.fetch(
            **search_args,
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        # Reformat results
        formatted_tag_info = []
        for tag in tags:
            info = {
                'id': tag['id'],
                'name': tag['name'],
                'description': tag['description'],
                'count': tag['count']
            }
            formatted_tag_info.append(info)

        formatted_tag_info.sort(key=lambda x: x['id'])

        file = pathing.Static.get_html("tag/list.html")
        result = serve(file)
        context = {
            'results': formatted_tag_info,
            'navbar': cls.get_navbar_context()
        }
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def view_tag(cls, request: Dict[str, Any]) -> ServeResponse:
        tag_id = request.get('GET').get('id')
        try:
            tag_id = int(tag_id)
        except (TypeError, ValueError):
            print("invalid tag id")
            return serve_error(400)

        client = dbapi.MasterClient(db_path=config.db_path)

        # Fetch tag info
        tags = client.tag.fetch(ids=[tag_id])
        if len(tags) != 1:
            print("bad results")
            return serve_error(404)
        tag = tags[0]

        # Reformat results
        formatted_tag_info = {
            'id': tag['id'],
            'name': tag['name'],
            'description': tag['description'],
            'count': tag['count']
        }

        serve_file = pathing.Static.get_html("tag/page.html")
        result = serve(serve_file)
        context = {
            'result': formatted_tag_info,
            'navbar': cls.get_navbar_context()
        }
        return reformat_serve(cls.renderer, result, context)

    @staticmethod
    def is_valid_page(display_page, page_size, total_items) -> bool:
        min_page = 1
        max_page = ceil(total_items / page_size)
        return min_page <= display_page <= max_page
