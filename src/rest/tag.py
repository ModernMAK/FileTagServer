from typing import Dict, Union, Tuple

import src.api as api
from src.api.common import SortQuery, parse_fields, Util
from src.api.tag import TagsQuery, TagQuery
from src.rest.common import serve_json, JsonResponse
from src.rest.models import RestTag
from src.rest.routes import tags, tag
from src.util.litespeedx import Response, Request

RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]


# Tags ===============================================================================================================
@tags.methods.get
def get_tags(request: Request) -> JsonResponse:
    args = request['GET']
    sort_args = SortQuery.parse_str(args.get('sort'))
    fields = parse_fields(args.get('fields'))
    query = TagsQuery(sort=sort_args, fields=fields)
    api_results = api.tag.get_tags(query)
    rest_results = RestTag.from_tag(api_results)
    return serve_json(Util.json(rest_results))

# @route(url=__tags, no_end_slash=True, methods=["POST"])
# def post_tags(request: Request) -> RestResponse:
#     body = request['BODY']
#     file_json = json.loads(body)
#     errors = []
#     req_fields = [__data_schema['name']]
#     opt_fields = [__data_schema['description']]
#     validate_fields(file_json, req_fields, opt_fields, errors)
#     populate_optional(file_json, opt_fields)
#
#     if len(errors) > 0:
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/tag/insert.sql")
#             cursor.execute(query, file_json)
#             conn.commit()
#             id = cursor.lastrowid
#             tag = {
#                 'id': id,
#                 'url': reformat_url(f"api/files/{id}"),
#             }
#         return JSend.success(tag), ResponseCode.CREATED, {'Location': tag['url']}
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])


# Tag ================================================================================================================
@tag.methods.get
def get_tag(request: Request, id: int) -> JsonResponse:
    args = request['GET']
    query = TagQuery (id=id,fields=args.get('fields'))
    api_result = api.tag.get_tag(query)
    rest_result = RestTag.from_tag(api_result)
    return serve_json(Util.json(rest_result))
#

# @route(__tag, no_end_slash=True, methods=["DELETE"])
# def delete_tag(request: Request, id: str) -> Dict:
#     try:
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/tag/delete_by_id.sql")
#             cursor.execute(query, id)
#             conn.commit()
#         return JSend.success(f"Deleted tag '{id}'")
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])
#
#
# @route(__tag, no_end_slash=True, methods=["PATCH"])
# def patch_file(request: Request, id: str) -> RestResponse:
#     body = request['BODY']
#     payload = json.loads(body)
#
#     required_fields = []
#     optional_fields = [__data_schema['name'], __data_schema['description']]
#
#     errors = []
#
#     if validate_fields(payload, required_fields, optional_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         parts: List[str] = [f"{key} = :{key}" for key in payload]
#         query = f"UPDATE tag SET {', '.join(parts)} WHERE id = :id"
#
#         payload['id'] = id
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             cursor.execute(query, payload)
#             conn.commit()
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])


# @route(__tag, no_end_slash=True, methods=["PUT"])
# def put_file(request: Request, id: str) -> RestResponse:
#     body = request['BODY']
#     payload = json.loads(body)
#
#     required_fields = [__data_schema['name'], __data_schema['description']]
#     opt_fields = []
#     errors = []
#
#     if validate_fields(payload, required_fields, opt_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         payload['id'] = id
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/tag/update.sql")
#             cursor.execute(query, payload)
#             conn.commit()
#
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])
