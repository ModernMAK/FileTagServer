import json
from typing import List, Dict, Union, Tuple, Type, Iterable

from src.api.models import File
from src.rest.routes import file, files, file_tags, files_tags, file_bytes
from src import config
from src.api.common import SortQuery, parse_fields, Util
from src.api.file import ValidationError, FilesQuery, FileQuery, CreateFileQuery
from src.rest.common import reformat_url, read_sql_file, validate_fields, populate_optional
from src.rest.models import RestFile, RestTag
from src.util.litespeedx import Response, Request, JSend
from sqlite3 import connect, Row, DatabaseError
from http import HTTPStatus as ResponseCode, HTTPStatus
import src.api as api

RestResponse = Union[Response, Tuple[Dict, int, Dict[str, str]]]

JsonResponse = Tuple[str, int, Dict[str, str]]


def serve_json(obj, status: int = 200, headers: Dict[str, str] = None, **dumps_kwargs) -> JsonResponse:
    content = obj if isinstance(obj, str) else json.dumps(obj, **dumps_kwargs)
    headers = headers or {}
    if 'content-type' not in headers:
        headers['content-type'] = 'application/json'
    return content, status, headers


# Files ===============================================================================================================
@files.methods.get
def get_files(request: Request) -> JsonResponse:
    # Parse individual api arguments; data is validated at the api level
    arguments: Dict[str, str] = request['GET']
    sort = SortQuery.parse_str(arguments.get("sort"))
    fields = parse_fields(arguments.get("fields"))
    tag_fields = parse_fields(arguments.get("tag_fields"))
    query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
    # Try api call; if invalid, fetch errors from validation error and return Bad Request
    api_results = api.file.get_files(query)
    rest_results = RestFile.from_file(api_results)
    return serve_json(Util.json(rest_results))



# @routes.files.methods.post
@files.methods.post
def post_files(request: Request) -> JsonResponse:
    body: str = request['BODY']
    body_json = json.loads(body)
    query = CreateFileQuery.parse_raw(body_json)
    api_result = api.file.create_file(query)
    rest_result = RestFile.from_file(api_result)
    return serve_json(rest_result.json(), HTTPStatus.Created, {'location': rest_result.urls.self})

    # errors = []
    # req_fields = [__data_schema['path']]
    # opt_fields = [__data_schema['name'], __data_schema['mime'], __data_schema['description']]
    # validate_fields(body_json, req_fields, opt_fields, errors)
    # populate_optional(body_json, opt_fields)

    # if len(errors) > 0:
    #     return JSend.fail(errors), ResponseCode.BAD_REQUEST
    # try:

    # except DatabaseError as e:
    #     return JSend.fail(e.args[0])


# Files Tags ==========================================================================================================
@files_tags.methods.get
def get_files_tags(request: Request):
    # Parse individual api arguments; data is validated at the api level
    arguments: Dict[str, str] = request['GET']
    sort = SortQuery.parse_str(arguments.get("sort"))
    fields = parse_fields(arguments.get("fields"))
    tag_fields = parse_fields(arguments.get("tag_fields"))
    query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
    # Try api call; if invalid, fetch errors from validation error and return Bad Request
    api_results = api.file.get_files_tags(query)
    rest_results = RestTag.from_tag(api_results)
    return serve_json(Util.json(rest_results))


# # Files Search ========================================================================================================
# @route(url=__files_search, no_end_slash=True, methods=["GET"])
# def get_files_search(request: Request) -> RestResponse:
#     def apply_get(path: str):
#         args: Dict = request['GET']
#         parts = [f"{k}={v}" for k, v in args.items()]
#         if len(parts) > 0:
#             return path + "?" + "&".join(parts)
#         return path
#
#     return b'', 301, {'Location': apply_get(reformat_url(__files))}


# File ================================================================================================================
# def __get_single_file_internal(cursor, id: str) -> Row:
#     query = read_sql_file("static/sql/file/select_by_id.sql")
#     cursor.execute(query, id)
#     rows = cursor.fetchall()
#     if len(rows) < 1:
#         raise ResponseError(ResponseCode.NOT_FOUND, f"No file found with the given id: '{id}'")
#     elif len(rows) > 1:
#         raise ResponseError(ResponseCode.MULTIPLE_CHOICES, f"Too many files found with the given id: '{id}'")
#     return rows[0]
#
#
@file.methods.get
def get_file(request: Request, id: int) -> JsonResponse:
    query = FileQuery(id=id)
    api_result = api.file.get_file(query)
    rest_result = RestFile.from_file(api_result)
    return serve_json(rest_result.json())


#
# @route(__file, no_end_slash=True, methods=["DELETE"])
# def delete_file(request: Request, id: str) -> RestResponse:
#     try:
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/file/delete_by_id.sql")
#             cursor.execute(query, id)
#             conn.commit()
#         return b'', ResponseCode.NO_CONTENT, {}  # , JSend.success(f"Deleted file '{id}'")
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])
#
#
# @route(__file, no_end_slash=True, methods=["PATCH"])
# def patch_file(request: Request, id: str) -> RestResponse:
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     required_fields = []
#     optional_fields = [__data_schema['name'], __data_schema['mime'], __data_schema['description'],
#                        __data_schema['path']]
#
#     errors = []
#
#     if validate_fields(file_json, required_fields, optional_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         parts: List[str] = [f"{key} = :{key}" for key in file_json]
#         query = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"
#
#         file_json['id'] = id
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             cursor.execute(query, file_json)
#             conn.commit()
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])
#
#
# @route(__file, no_end_slash=True, methods=["PUT"])
# def put_file(request: Request, id: str) -> RestResponse:
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     required_fields = [__data_schema['name'], __data_schema['path'], __data_schema['mime'],
#                        __data_schema['description']]
#     opt_fields = []
#     errors = []
#
#     if validate_fields(file_json, required_fields, opt_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         file_json['id'] = id
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/file/update.sql")
#             cursor.execute(query, file_json)
#             conn.commit()
#
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.error(e.args[0]), ResponseCode.INTERNAL_SERVER_ERROR
#
#
# # File Tags ===========================================================================================================
@file_tags.methods.get
def get_file_tags(request: Request, id: int) -> JsonResponse:
    q = FileQuery(id=id)
    api_result = api.file.get_file_tags(q)
    rest_result = RestTag.from_tag(api_result)
    return serve_json(Util.json(rest_result))

#
# # SET
# @route(__file_tags, no_end_slash=True, methods=["PUT"])
# def put_file_tags(request: Request, id: str):
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     required_fields = [__data_schema['tags']]
#     opt_fields = []
#     errors = []
#     if validate_fields(file_json, required_fields, opt_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         insert_args = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
#         delete_sub = ', '.join('?' * len(file_json['tags']))
#         delete_query = f"DELETE FROM file_tag WHERE file_tag.file_id = ? AND file_tag.tag_id NOT IN ({delete_sub});"
#         insert_query = f"INSERT OR IGNORE INTO file_tag (file_id, tag_id) VALUES (:file_id,:tag_id);"
#         delete_args = [id] + file_json['tags']
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             cursor.execute(delete_query, delete_args)
#             cursor.executemany(insert_query, insert_args)
#             conn.commit()
#             return JSend.success(""), ResponseCode.NO_CONTENT
#     except DatabaseError as e:
#         return JSend.fail(e.args[0]), ResponseCode.INTERNAL_SERVER_ERROR
#
#
# # REMOVE
# @route(__file_tags, no_end_slash=True, methods=["DELETE"])
# def delete_file_tags(request: Request, id: str):
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     required_fields = [__data_schema['tags']]
#     opt_fields = []
#     errors = []
#     if validate_fields(file_json, required_fields, opt_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/file_tag/delete_pair.sql")
#             cursor.executemany(query, file_tag_pairs)
#             conn.commit()
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])
#
#
# # ADD
# @route(__file_tags, no_end_slash=True, methods=["POST"])
# def post_file_tags(request: Request, id: str):
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     required_fields = [__data_schema['tags']]
#     opt_fields = []
#     errors = []
#     if validate_fields(file_json, required_fields, opt_fields, errors):
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
#         with connect(config.db_path) as conn:
#             conn.execute("PRAGMA foreign_keys = 1")
#             cursor = conn.cursor()
#             query = read_sql_file("static/sql/file_tag/insert.sql")
#             cursor.executemany(query, file_tag_pairs)
#             conn.commit()
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e.args[0])
#
#
# # This is just a merged post/delete
# # # UPDATE
# # @route(__file_tags, no_end_slash=True, methods=["PATCH"])
# # def patch_file_tags(request: Request, id: str):
# #     pass
#
# # FILE DATA ================================================================================================= FILE DATA
# @route(__file_data, no_end_slash=True, methods=["GET"])
# def get_file_data(request: Request, id: str):
#     try:
#         id = int(id)
#         range = request['HEADERS'].get('Range')
#         return api.file.get_file_bytes(id, range)
#     except ResponseError as e:
#         return JSend.fail(e.message), e.code
#
#
# # api REFERENCE ========================================================================================= api REFERENCE
# @route(__reference, no_end_slash=True, methods=["GET"])
# def reference_files(request: Request):
#     pass
#
#
# @route(__reference + "/(.+)", methods=["GET"])
# def reference_redirect(request: Request):
#     url = reformat_url(__reference)
#     return url, ResponseCode.SEE_OTHER, {'Location': url}
