from typing import Dict, Any

from litespeed import serve
from pystache import Renderer

import src.database_api.clients  as dbapi
from src import config
from src.page_groups import pathing, routing
from src.page_groups.page_group import PageGroup, ServeResponse
from src.page_groups.shared_page_util import get_navbar_context
from src.page_groups.status_code_page_group import StatusPageGroup
from src.util.collection_util import get_unique_values_on_key
from src.util.page_utils import reformat_serve


class FilePageGroup(PageGroup):
    renderer = None

    @classmethod
    def add_routes(cls):
        get_only = ['GET']
        cls._add_route(routing.WebRoot.root, function=cls.index, methods=get_only)
        cls._add_route(routing.FilePage.root, function=cls.index, methods=get_only)
        cls._add_route(routing.FilePage.index_list, function=cls.view_as_list, methods=get_only)
        cls._add_route(routing.FilePage.view_file, function=cls.view_file, methods=get_only)
        cls._add_route(routing.FilePage.serve_file_raw, function=cls.serve_raw_file, methods=get_only)
        cls._add_route(routing.FilePage.serve_page_raw, function=cls.serve_raw_page, methods=get_only)
        cls._add_route(routing.FilePage.slideshow, function=cls.serve_slideshow, methods=get_only)

    @classmethod
    def initialize(cls, **kwargs):
        cls.renderer = Renderer(search_dirs=[config.template_path])

    #########
    # Displays the primary page of the file page group
    # This should almost always either be;
    #   A splash-screen main page for the group
    #   A homepage for the topics of the group
    #   An alias for primary page of the group (deferring to that page display)
    #########
    @classmethod
    def index(cls, request: Dict[str, Any]) -> ServeResponse:
        print("file page index")
        return StatusPageGroup.serve_redirect(301, routing.FilePage.index_list)
        # return cls.view_as_list(request)

    #########
    # Displays the files in the file_page database as a list
    # This is primarily intended to be used to edit multiple file's tags at once
    # GET SUPPORT:
    #   Pagination ~ Page # Only => 'page'
    #       page counts from 1; to reflect the UI
    #########
    @classmethod
    def view_as_list(cls, request: Dict[str, Any]) -> ServeResponse:
        print("file page list")
        page = int(request.get('GET').get('page', 1))
        client = dbapi.MasterClient(db_path=config.db_path)
        page_size = 50
        search_args = {}

        # Count files
        file_count = client.file.count(**search_args)
        # Determine if page is valid
        if not cls.is_page_valid(page, page_size, file_count) and page != 1:
            return StatusPageGroup.serve_error(404)

        # Fetch results for page
        files = client.file.fetch(
            **search_args,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        # grab unique ids
        unique_ids = get_unique_values_on_key(files, 'id')
        # fetch file to tag lookup
        file_tags = client.map.fetch_lookup_groups(key='file_id', files=unique_ids)
        # fetch unique tags
        unique_tag_ids = set()
        for tagged_file in file_tags.values():
            for pair in tagged_file:
                unique_tag_ids.add(pair['tag_id'])
        # fetch tag lookup
        tag_lookup = client.tag.fetch_lookup(ids=unique_tag_ids)

        # Reformat results
        formatted_tag_info_lookup = {}
        for id in unique_tag_ids:
            pair = tag_lookup[id]
            formatted_tag_info_lookup[id] = {
                'id': pair['id'],
                'name': pair['name'],
                'description': pair['description'],
                'count': pair['count'],
                'page_path': routing.TagPage.get_view_tag(pair['id'])
            }
        formatted_tag_info = [v for v in formatted_tag_info_lookup.values()]

        formatted_tag_info.sort(key=lambda x: (-x['count'], x['name']))

        formatted_file_info = []
        for file in files:
            print(file)
            f_id = file['id']
            my_tags = []
            for pair in file_tags.get(f_id, []):
                tag_id = pair['tag_id']
                my_tags.append(formatted_tag_info_lookup[tag_id])
            my_tags.sort(key=lambda x: x['name'])

            info = {
                'id': file['id'],
                'path': file['path'],
                'mime': file['mime'],
                'name': file['name'],
                'description': file['description'],
                'tags': my_tags,
                'page_path': routing.FilePage.get_view_file(file['id']),
                'raw_file_path': routing.FilePage.get_serve_file_raw(file['id'])
            }
            formatted_file_info.append(info)

        file = pathing.Static.get_html("file/list.html")
        print(file)
        result = serve(file)
        context = {
            'page_title': "Files",
            'results': formatted_file_info,
            'tags': formatted_tag_info,
            'navbar': get_navbar_context(active=routing.FilePage.root),
            'subnavbar': {'list': 'active'}
        }
        return reformat_serve(cls.renderer, result, context)

    #########
    # Displays the files in the file_page database as a list
    # This is primarily intended to be used to edit multiple file's tags at once
    # GET SUPPORT:
    #   Pagination ~ Page # Only => 'page'
    #       page counts from 1; to reflect the UI
    #########
    @classmethod
    def view_file(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request['GET'].get('id')
        try:
            file_id = int(file_id)
        except (ValueError, TypeError):
            print(f"invalid file id: {file_id}")
            return StatusPageGroup.serve_error(400)

        client = dbapi.MasterClient(db_path=config.db_path)

        # Fetch file info
        files = client.file.fetch(ids=[file_id])
        if len(files) != 1:
            print("bad results")
            return StatusPageGroup.serve_error(404)
        file = files[0]

        # fetch file to tag lookup
        file_tags = client.map.fetch_lookup_groups(key='file_id', files=[file_id])
        # fetch unique tags
        unique_tag_ids = set()
        for tagged_file in file_tags.values():
            for pair in tagged_file:
                unique_tag_ids.add(pair['tag_id'])
        # fetch tag lookup
        tag_lookup = client.tag.fetch_lookup(ids=unique_tag_ids)

        # Reformat results
        formatted_tag_info_lookup = {}
        for id in unique_tag_ids:
            pair = tag_lookup[id]
            formatted_tag_info_lookup[id] = {
                'id': pair['id'],
                'name': pair['name'],
                'description': pair['description'],
                'count': pair['count'],
                'page_path': routing.TagPage.get_view_tag(pair['id'])
            }
        formatted_tag_info = [v for v in formatted_tag_info_lookup.values()]

        formatted_tag_info.sort(key=lambda x: (-x['count'], x['name']))

        my_tags = []
        for pair in file_tags.get(file_id, []):
            tag_id = pair['tag_id']
            my_tags.append(formatted_tag_info_lookup[tag_id])
        my_tags.sort(key=lambda x: x['name'])

        formatted_file_info = {
            'id': file['id'],
            'file_path': file['path'],
            'mime': file['mime'],
            'name': file['name'],
            'description': file['description'],
            'tags': my_tags,
            'raw_file_path': routing.FilePage.get_serve_file_raw(file['id']),
            'page_path': routing.FilePage.get_view_file(file['id'])
        }

        serve_file = pathing.Static.get_html("file/page.html")
        result = serve(serve_file)
        context = {
            'result': formatted_file_info,
            'tags': formatted_tag_info,
            'navbar': get_navbar_context(),
            'subnavbar': {}
        }
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def serve_raw_file(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request.get('GET').get('id')
        client = dbapi.MasterClient(db_path=config.db_path)
        results = client.file.fetch(ids=[file_id])
        if len(results) == 0:
            return StatusPageGroup.serve_error(404)
        else:
            return serve(results[0]['path'], range=request.get("range", "bytes=0-"))

    @classmethod
    def serve_raw_page(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request.get('GET').get('id')
        client = dbapi.MasterClient(db_path=config.db_path)
        results = client.file.fetch(ids=[file_id])
        if len(results) == 0:
            return StatusPageGroup.serve_error(404)
        else:
            result = results[0]
            # print(result)
            mime = result['mime']
            # print(mime)
            # .split("/")[0]
            mime = mime.split("/")
            if len(mime) > 0:
                mime = mime[0]
            else:
                mime = ""

            raw_url = routing.FilePage.get_serve_file_raw(result['id'])
            if mime == "image":
                serve_file = pathing.Static.get_html("raw/image.html")
                ctx = {
                    "title": result['name'],
                    "source": raw_url
                }
                s = serve(serve_file)
                return reformat_serve(cls.renderer, s, ctx)
            else:
                return StatusPageGroup.serve_error(404)

    @classmethod
    def serve_slideshow(cls, request: Dict[str, Any]) -> ServeResponse:
        file_id = request.get('GET').get('id')
        client = dbapi.MasterClient(db_path=config.db_path)
        results = client.file.fetch(ids=[file_id])
        if len(results) == 0:
            return StatusPageGroup.serve_error(404)
        else:
            result = results[0]
            mime = result['mime'].split("/")
            if len(mime) > 0:
                mime = mime[0]
            else:
                mime = ""

            raw_url = routing.FilePage.get_serve_file_raw(result['id'])
            serve_file = pathing.Static.get_html("file/ss.html")
            if mime == "image":
                ctx = {
                    "title": result['name'],
                    "image": {
                        "alt": result['description'],
                        "source": raw_url
                    }
                }
                s = serve(serve_file)
                return reformat_serve(cls.renderer, s, ctx)
            elif mime == "video":
                ctx = {
                    "title": result['name'],
                    "video": {
                        "alt": result['description'],
                        "source": raw_url,
                        "mime": result['mime']
                    }
                }
                s = serve(serve_file)
                return reformat_serve(cls.renderer, s, ctx)
            else:
                return StatusPageGroup.serve_error(404)