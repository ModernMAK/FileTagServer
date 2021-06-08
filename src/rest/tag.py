import json
from http import HTTPStatus
from typing import Dict, Union, Tuple, Any

from src.FileTagServer.API.common import SortQuery, parse_fields, Util
from src.FileTagServer.API.tag import TagsQuery, TagQuery, DeleteTagQuery, ModifyTagQuery, SetTagQuery, CreateTagQuery
from src.rest.common import serve_json, JsonResponse
from src.rest.routes import tags, tag, tag_autocomplete
from src.util.litespeedx import Response, Request

RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]


def setup_routes():
    """
    A Dummy Function To ensure endpoints have been loaded.
    The endpoints must be finalized by calling .route(*args,**kwargs)
    """
    pass

# Tags ===============================================================================================================
@tags.methods.get
def get_tags(request: Request) -> JsonResponse:
    args = request['GET']
    sort_args = SortQuery.parse_str(args.get('sort'))
    fields = parse_fields(args.get('fields'))
    query = TagsQuery(sort=sort_args, fields=fields)
    api_results = src.FileTagServer.API.tag.get_tags(query)
    return serve_json(Util.json(api_results))


@tags.methods.post
def post_tags(request: Request) -> JsonResponse:
    body = request['BODY']
    payload = json.loads(body)
    query = CreateTagQuery(**payload)
    return serve_json(Util.json(src.FileTagServer.API.tag.create_tag(query)))


# Tag ================================================================================================================
@tag.methods.get
def get_tag(request: Request, id: int) -> JsonResponse:
    args = request['GET']
    query = TagQuery(id=id, fields=args.get('fields'))
    api_result = src.FileTagServer.API.tag.get_tag(query)
    return serve_json(Util.json(api_result))


@tag.methods.delete
def delete_tag(request: Request, id: int) -> RestResponse:
    query = DeleteTagQuery(id=id)
    if src.FileTagServer.API.tag.delete_tag(query):
        return b'', HTTPStatus.Ok, {}
    else:
        return b'', HTTPStatus.BAD_REQUEST, {}


@tag.methods.patch
def patch_tag(request: Request, id: int) -> RestResponse:
    body = request['BODY']
    payload = json.loads(body)
    query = ModifyTagQuery(id=id, **payload)
    if src.FileTagServer.API.tag.modify_tag(query):
        return b'', HTTPStatus.NO_CONTENT, {}
    else:
        return b'', HTTPStatus.BAD_REQUEST, {}


@tag.methods.put
def put_tag(request: Request, id: int) -> RestResponse:
    body = request['BODY']
    payload = json.loads(body)
    query = SetTagQuery(id=id, **payload)
    if src.FileTagServer.API.tag.set_tag(query):
        return b'', HTTPStatus.NO_CONTENT, {}
    else:
        return b'', HTTPStatus.BAD_REQUEST, {}


def __shared_autocomplete_tags(request: Request, payload: Dict[str, Any]):
    api_result = src.FileTagServer.API.tag.autocomplete_tag(payload.get('name'))
    r = serve_json(Util.json(api_result))
    c, _, _ = r
    print(c)
    return r


@tag_autocomplete.methods.post
def autocomplete_tags(request: Request) -> JsonResponse:
    try:
        body = request['BODY']
        payload = json.loads(body)
        return __shared_autocomplete_tags(request, payload)
    except Exception as e:
        print(e)
        raise


@tag_autocomplete.methods.get
def autocomplete_tags(request: Request) -> JsonResponse:
    try:
        payload = request['GET']
        return __shared_autocomplete_tags(request, payload)
    except Exception as e:
        print(e)
        raise
