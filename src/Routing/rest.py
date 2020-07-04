from io import StringIO
from typing import Dict, List, Any, Tuple, Union
import configparser
from litespeed import route, serve
import dicttoxml
from pystache import Renderer

from src import PathUtil
from src.API.ModelClients import FilePage as FilePageClient, Tag as TagClient
from src.API.Models import BaseModel

database_path = None
renderer = None


def initialize_module(**kwargs):
    global renderer
    global database_path
    config = kwargs.get('config', {})
    launch_args = config.get('Launch Args', {})
    search_dirs = launch_args.get('template_dirs', [PathUtil.html_real_path("templates")])
    renderer = Renderer(search_dirs=search_dirs)
    database_path = launch_args.get('db_path', PathUtil.data_real_path('mediaserver.db'))


def add_routes():
    route(r'/rest/file/(\d+)', no_end_slash=True, f=rest_file_get, methods=['GET'])
    route(r'/rest/tag/(\d+)', no_end_slash=True, f=rest_tag_get, methods=['GET'])


def __convert_to_dict_list(info_list: List[BaseModel]) -> List[Dict[str, Any]]:
    if not info_list:
        return []
    results = []
    for info in info_list:
        results.append(dict(info))
    return results


def __get_request_format(request):
    get_args = request['GET']
    return get_args.get('format', 'html')


def format_data(data, request_format):
    if request_format == 'json':
        return json.dumps(data)
    elif request_format == 'xml':
        return dicttoxml.dicttoxml(data)
    elif request_format == 'ini':
        config = configparser.ConfigParser()
        config.read_dict({'ROOT': data})
        with StringIO() as stream:
            config.write(stream)
            return stream.getvalue()
    else:
        return None


def serve_rest(data, request_format: Tuple[Union[str, None], Union[str, None]], html_page=None):
    if not isinstance(data, dict):
        data = dict(data)

    if request_format == 'html':
        if html_page is not None:
            context = data
            body, status, header = serve(PathUtil.html_real_path(html_page))
            if status == 200:
                body = renderer.render(body, context)
            return body, status, header
        else:
            return data
    else:
        body = format_data(data, request_format)

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
    return serve_rest(results[0], request_format, html_page='rest/tag.html')


def rest_file_get(request, img_id):
    client = FilePageClient(db_path=database_path)
    request_format = __get_request_format(request)
    results = client.get(ids=[int(img_id)])
    if len(results) != 1:
        return None, 404
    return serve_rest(results[0], request_format, html_page='rest/file.html')
