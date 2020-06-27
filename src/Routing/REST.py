from io import StringIO
from typing import Dict, List, Any, Tuple, Union
import configparser
from litespeed import route
import dicttoxml
import src.DbMediator as DbUtil
from src.API.Clients import ImageClient, TagClient
from src.API.Models import BaseModel
import json as json

database_path = DbUtil.database_path
GET_ONLY = ['GET']
GET_AND_POST = ['GET', 'POST']
POST_ONLY = ['POST']


def add_routes():
    route(r'/rest/image/(\d+)', no_end_slash=True, f=rest_image_get, methods=GET_ONLY)
    route(r'/rest/tag/(\d+)', no_end_slash=True, f=rest_tag_get, methods=GET_ONLY)
    pass


def __convert_to_dict_list(info_list: List[BaseModel]) -> List[Dict[str, Any]]:
    if not info_list:
        return []
    results = []
    for info in info_list:
        results.append(dict(info))
    return results


def __get_request_format(request):
    get_args = request['GET']
    raw_request_format = get_args.get('format', 'html-json')
    temp = raw_request_format.split('-')
    base_format = None
    sub_format = None
    if len(temp) > 0:
        base_format = temp[0].lower()
    if len(temp) > 1:
        sub_format = temp[1].lower()

    return base_format, sub_format


def format_data(data, request_format: str):
    if not isinstance(data, dict):
        data = dict(data)

    if request_format == 'json':
        return json.dumps(data)
    elif request_format == 'xml':
        return dicttoxml.dicttoxml(data)
    elif request_format == 'ini':  # ~ Why would anyone need this? Nobody would, but somebody issued a challenge and i gave up on said challenge
        config = configparser.ConfigParser()
        config.read_dict({'ROOT': data})
        with StringIO() as stream:
            config.write(stream)
            return stream.getvalue()
    else:
        return None


def serve_rest(data, request_format: Tuple[Union[str, None], Union[str, None]]):
    if request_format[0] == 'html':
        body = format_data(data, request_format[1])
        if body:
            body = body.replace('\n', '<br>')
            body = body.replace(' ', '&nbsp;')
            return body, 200, None
    else:
        return format_data(data, request_format[0])
    return None, 400, None


def rest_image_get(request, tag_id):
    client = TagClient(database_path)
    request_format = __get_request_format(request)
    results = client.get_tags(tag_ids=[int(tag_id)])
    if len(results) != 1:
        return None, 404
    return serve_rest(results[0], request_format)


def rest_tag_get(request, img_id):
    client = ImageClient(database_path)
    request_format = __get_request_format(request)
    results = client.get_images(image_ids=[int(img_id)])
    if len(results) != 1:
        return None, 404

    return serve_rest(results[0], request_format)
