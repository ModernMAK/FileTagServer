from io import StringIO
from typing import Dict, List, Any, Tuple, Union
import configparser
from litespeed import route, serve
import dicttoxml
from pystache import Renderer

from src.routing.virtual_access_points import RequiredVap
from src.util import path_util, dict_util
from src.api.model_clients import FilePage as FilePageClient, Tag as TagClient
from src.api.models import BaseModel
from src.util.dict_util import DictFormat

database_path = None
renderer = None


def initialize_module(**kwargs):
    global renderer
    global database_path
    config = kwargs.get('config', {})
    launch_args = config.get('Launch Args', {})
    search_dirs = launch_args.get('template_dirs', [RequiredVap.html_real("templates")])
    renderer = Renderer(search_dirs=search_dirs)
    database_path = launch_args.get('db_path', RequiredVap.html_real('mediaserver.db'))


def add_routes():
    route(r'/rest/file/(\d+)', no_end_slash=True, function=rest_file_get, methods=['GET'])
    route(r'/rest/tag/(\d+)', no_end_slash=True, function=rest_tag_get, methods=['GET'])


def __convert_to_dict_list(info_list: List[BaseModel]) -> List[Dict[str, Any]]:
    if not info_list:
        return []
    results = []
    for info in info_list:
        results.append(dict(info))
    return results


def __get_request_format(request) -> Union[DictFormat, None]:
    get_args = request['GET']
    format = get_args.get('format', 'html')
    try:
        return DictFormat[format]
    except:
        return None


def serve_rest(data: Any, request_format: DictFormat, html_page=None):
    if not isinstance(data, dict):
        data = dict(data)

    if request_format is None:
        if html_page is not None:
            context = data
            body, status, header = serve(RequiredVap.rest_html_real_def(html_page))
            if status == 200:
                body = renderer.render(body, context)
            return body, status, header
        else:
            return data
    else:
        body = dict_util.dict_to_str(data, request_format)

        if body is not None:
            return body, 200
        else:
            return body, 400


def rest_tag_get(request, tag_id):
    client = TagClient(db_path=database_path)
    request_format = __get_request_format(request)
    results = client.get(tag_ids=[int(tag_id)])
    if len(results) != 1:
        return None, 404
    return serve_rest(results[0], request_format, html_page='tag.html')


def rest_file_get(request, img_id):
    client = FilePageClient(db_path=database_path)
    request_format = __get_request_format(request)
    results = client.get(ids=[int(img_id)])
    if len(results) != 1:
        return None, 404
    return serve_rest(results[0], request_format, html_page='file.html')
