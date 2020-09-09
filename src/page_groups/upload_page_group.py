from typing import Callable, List, Dict, Any

from litespeed import route, serve
from pystache import Renderer

from src import config
from src.page_groups.shared_page_util import get_navbar_context
from src.page_groups.page_group import PageGroup, ServeResponse, ServeFunction
from src.util.page_utils import reformat_serve
from src.page_groups import routing, pathing
from src.page_groups.status_code_page_group import StatusPageGroup, HTTPStatus


class UploadGroup(PageGroup):
    renderer = None

    @classmethod
    def add_routes(cls):
        def helper(path, func, methods=None):
            route(path,
                  function=cls.as_route_func(func),
                  no_end_slash=True,
                  methods=methods)

        helper(routing.UploadPage.root, cls.index, ['GET'])

        helper(routing.UploadPage.upload_file, cls.upload_files, ['GET'])
        helper(routing.UploadPage.action_upload_file, cls.action_upload_files, ['POST'])

        helper(routing.UploadPage.add_file, cls.add_files, ['GET'])
        helper(routing.UploadPage.action_add_file, cls.action_add_files, ['POST'])

        # route(routing.UploadPage.upload_file,
        #       function=cls.as_route_func(cls.upload_files),
        #       no_end_slash=True,
        #       methods=['GET'])
        #
        # route(routing.UploadPage.action_add_file,
        #       function=cls.as_route_func(cls.action_add_files),
        #       no_end_slash=True,
        #       methods=['POST'])
        #
        # route(routing.UploadPage.add_file,
        #       function=cls.as_route_func(cls.add_files),
        #       no_end_slash=True,
        #       methods=['GET'])

    @classmethod
    def initialize(cls, **kwargs):
        cls.renderer = Renderer(search_dirs=[config.template_path])

    @classmethod
    def index(cls, request):
        return StatusPageGroup.serve_redirect(HTTPStatus.TEMPORARY_REDIRECT, routing.UploadPage.upload_file)

    @classmethod
    def upload_files(cls, request) -> ServeResponse:
        result = serve(pathing.Static.get_html('upload/upload_file.html'))
        context = {
            'navbar': get_navbar_context(active="Upload"),
            'action_path': routing.UploadPage.action_upload_file
        }
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def action_upload_files(cls, request) -> ServeResponse:
        files = request.get('FILES')
        for k, v in request.items():
            print(f"{k}\t\t\t{v}")
        if len(files) == 0:
            return StatusPageGroup.serve_redirect(HTTPStatus.SEE_OTHER, routing.UploadPage.upload_file)
        for file in files:
            print(file)

        return StatusPageGroup.serve_redirect(HTTPStatus.SEE_OTHER, routing.UploadPage.upload_file)

    @classmethod
    def add_files(cls, request) -> ServeResponse:
        result = serve(pathing.Static.get_html('upload/add_file.html'))
        context = {
            'navbar': get_navbar_context(active="Upload"),
            'action_path': routing.UploadPage.action_add_file
        }
        return reformat_serve(cls.renderer, result, context)

    @classmethod
    def action_add_files(cls, request) -> ServeResponse:
        post = request.get('POST')
        files = request.get('FILES')

        if 'paths' in post:
            print(post.get('paths'))
        elif len(files) > 0:
            print(files)
        else:
            return StatusPageGroup.serve_redirect(HTTPStatus.SEE_OTHER, routing.UploadPage.add_file)

        return StatusPageGroup.serve_redirect(HTTPStatus.SEE_OTHER, routing.UploadPage.add_file)
