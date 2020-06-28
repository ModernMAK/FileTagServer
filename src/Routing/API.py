from typing import Dict, Optional, Tuple, Union, Callable, List, Any

from PIL import Image
from litespeed import serve, route, register_error_page
from pystache import Renderer
from src.API.Clients import ImageClient, TagClient, ApiClient
from src.API.Models import BaseModel
import src.PathUtil as PathUtil
import src.DbMediator as DbUtil

database_path = DbUtil.database_path
JSON_HEADERS = "Content-Type: application/json"


def add_routes():
    route(f'/api/image/get', no_end_slash=True, f=api_image_get, methods=['GET'])
    pass


def __convert_to_dict_list(info_list: List[BaseModel]) -> List[Dict[str, Any]]:
    if not info_list:
        return []
    results = []
    for info in info_list:
        results.append(info.to_dictionary())
    return results


def api_image_get(request):
    client = ImageClient(database_path)
    get = request['GET']
    context = client.get_images(**get)

    img_list = __convert_to_dict_list(context)
    json = {
        'Images': img_list
    }
    return json, 200, JSON_HEADERS
