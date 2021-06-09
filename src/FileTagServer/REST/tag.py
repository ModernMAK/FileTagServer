from typing import Optional, List

from starlette import status

from FileTagServer.DBI import tag as tag_api
from FileTagServer.DBI.common import parse_fields, SortQuery, AutoComplete
from FileTagServer.DBI.models import Tag
from FileTagServer.DBI.tag import TagsQuery, CreateTagQuery, TagQuery, DeleteTagQuery, ModifyTagQuery, \
    FullModifyTagQuery, SetTagQuery, FullSetTagQuery
from FileTagServer.REST.routing import tags_route, tag_route, tag_files_route, tags_search_route, tags_autocomplete
from FileTagServer.REST.common import rest_api


tags_metadata = [
    {"name": "Tags", "description": ""},
    {"name": "Tag", "description": ""},
]



# Tags ===============================================================================================================
@rest_api.get(tags_route)
def get_tags(sort: Optional[str] = None, fields: Optional[str] = None) -> List[Tag]:
    sort_args = SortQuery.parse_str(sort)
    fields = parse_fields(fields)
    query = TagsQuery(sort=sort_args, fields=fields)
    api_results = tag_api.get_tags(query)
    return api_results


@rest_api.post(tags_route)
def post_tags(query: CreateTagQuery) -> Tag:
    api_result = tag_api.create_tag(query)
    return api_result


# Tag ================================================================================================================
@rest_api.get(tag_route)
def get_tag(tag_id: int, fields: Optional[str] = None) -> Tag:
    query = TagQuery(id=tag_id, fields=fields)
    api_result = tag_api.get_tag(query)
    return api_result


@rest_api.delete(tag_route, status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int):
    query = DeleteTagQuery(id=tag_id)
    tag_api.delete_tag(query)
    # if tag_api.delete_tag(query):
    #     return b'', HTTPStatus.Ok, {}
    # else:
    #     return b'', HTTPStatus.BAD_REQUEST, {}


@rest_api.patch(tag_route)
def patch_tag(tag_id: int, request: ModifyTagQuery):
    query = FullModifyTagQuery(id=tag_id, **request.dict())
    tag_api.modify_tag(query)
    # if tag_api.modify_tag(query):
    #     return b'', HTTPStatus.NO_CONTENT, {}
    # else:
    #     return b'', HTTPStatus.BAD_REQUEST, {}


@rest_api.put(tag_route)
def put_tag(tag_id: int, request: SetTagQuery):
    query = FullSetTagQuery(id=tag_id, **request.dict())
    tag_api.set_tag(query)
    # if tag_api.set_tag(query):
    #     return b'', HTTPStatus.NO_CONTENT, {}
    # else:
    #     return b'', HTTPStatus.BAD_REQUEST, {}


# def __shared_autocomplete_tags(payload: Dict[str, Any]):
#     api_result = tag_api.autocomplete_tag(payload.get('name'))
#     return api_result
#     # r = serve_json(Util.json(api_result))
#     # c, _, _ = r
#     # print(c)
#     # return r


@rest_api.get(tags_autocomplete)
@rest_api.post(tags_autocomplete)
def autocomplete_tags(name: str) -> List[AutoComplete]:
    return tag_api.autocomplete_tag(name)
    # try:
    #     body = request['BODY']
    #     payload = json.loads(body)
    #     return __shared_autocomplete_tags(request, payload)
    # except Exception as e:
    #     print(e)
    #     raise

#
# @tag_autocomplete.methods.get
# def autocomplete_tags(request: Request) -> JsonResponse:
#     try:
#         payload = request['GET']
#         return __shared_autocomplete_tags(request, payload)
#     except Exception as e:
#         print(e)
#         raise
