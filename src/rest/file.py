import json
from http import HTTPStatus
from typing import Dict, Union, Tuple

from litespeed.error import ResponseError
from pydantic import ValidationError

import src.api as api
from src import config
from src.api.common import SortQuery, parse_fields, Util
from src.api.file import FilesQuery, FileQuery, CreateFileQuery, FileDataQuery, FileTagQuery, DeleteFileQuery, \
    ModifyFileQuery, SetFileQuery
from src.rest.common import JsonResponse, serve_json
from src.rest.routes import file, files, file_tags, files_tags, file_bytes, files_search
from src.util.litespeedx import Response, Request

RestResponse = Union[Response, Tuple[Dict, int, Dict[str, str]]]


# Files ===============================================================================================================
@files.methods.get(allow_cors=True)
def get_files(request: Request) -> JsonResponse:
    # Parse individual api arguments; data is validated at the api level
    arguments: Dict[str, str] = request['GET']
    sort = SortQuery.parse_str(arguments.get("sort"))
    fields = parse_fields(arguments.get("fields"))
    tag_fields = parse_fields(arguments.get("tag_fields"))
    try:
        query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
    except ValidationError as e:
        return serve_json(e.json(), HTTPStatus.BAD_REQUEST)

    # Try api call; if invalid, fetch errors from validation error and return Bad Request
    api_results = api.file.get_files(query)
    return serve_json(Util.json(api_results))


@files.methods.post
def post_files(request: Request) -> JsonResponse:
    body: str = request['BODY']
    query = CreateFileQuery.parse_obj(json.loads(body))
    api_result = api.file.create_file(query)
    return serve_json(api_result.json(), HTTPStatus.Created, {'location': config.resolve_url(file.path(api_result.id))})


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
    return serve_json(Util.json(api_results))


# Files Search ========================================================================================================
@files_search.methods.get
def get_files_search(request: Request) -> RestResponse:
    def apply_get(path: str):
        args: Dict = request['GET']
        parts = [f"{k}={v}" for k, v in args.items()]
        if len(parts) > 0:
            return path + "?" + "&".join(parts)
        return path

    return b'', 301, {'Location': config.resolve_url(apply_get(files.path()))}


# File ================================================================================================================
@file.methods.get
def get_file(request: Request, id: int) -> JsonResponse:
    try:
        query = FileQuery(id=id)
    except ValidationError as e:
        return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
    try:
        api_result = api.file.get_file(query)
        return serve_json(api_result.json())
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:  # SEE get_file_bytes for why we do this
            raise ResponseError(HTTPStatus.GONE)
        else:
            raise


@file.methods.delete
def delete_file(request: Request, id: int) -> Union[RestResponse,JsonResponse]:
    try:
        query = DeleteFileQuery(id=id)
    except ValidationError as e:
        return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
    try:
        success = api.file.delete_file(query)
        if success:
            return b'', HTTPStatus.NO_CONTENT, {}
        else:
            return b'', HTTPStatus.INTERNAL_SERVER_ERROR, {}
    except ResponseError as e:
        if e.code == 404:
            raise ResponseError(HTTPStatus.GONE)
        else:
            raise


#
#
@file.methods.patch
def patch_file(request: Request, id: str) ->  Union[RestResponse,JsonResponse]:
    body = request['BODY']
    body_json = json.load(body)
    body_json['id'] = id
    try:
        query = ModifyFileQuery.parse_obj(body_json)
    except ValidationError as e:
        return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
    try:
        api.file.modify_file(query)
        return b'', HTTPStatus.NO_CONTENT, {}
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:
            raise ResponseError(HTTPStatus.GONE)
        else:
            raise


#
@file.methods.put
def put_file(request: Request, id: int) -> Union[RestResponse,JsonResponse]:
    body = request['BODY']
    body_json = json.loads(body)
    body_json['id'] = id
    try:
        query = SetFileQuery.parse_obj(body_json)
    except ValidationError as e:
        return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
    try:
        success = api.file.set_file(query)
        return b'', HTTPStatus.NO_CONTENT if success else HTTPStatus.INTERNAL_SERVER_ERROR, {}
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:
            raise ResponseError(HTTPStatus.GONE)
        else:
            raise


# File Tags ===========================================================================================================
@file_tags.methods.get
def get_file_tags(request: Request, id: int) -> JsonResponse:
    q = FileTagQuery(id=id)
    try:
        api_result = api.file.get_file_tags(q)
        return serve_json(Util.json(api_result))
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:  # SEE get_file_bytes for why we do this
            raise ResponseError(HTTPStatus.GONE)
        else:
            raise


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
# FILE DATA ================================================================================================= FILE DATA
@file_bytes.methods.get
def get_file_data(request: Request, id: int):
    range = request['HEADERS'].get('Range')
    query = FileDataQuery(id=id, range=range)
    try:
        return api.file.get_file_bytes(query)
    except ResponseError as e:
        if e.code == 404:
            # The 'least smelly' IMO response
            # I'd prefer 404 ONLY be used when the endpoint itself does not exist
            #   Therefore if a function in the rest api is called, it cannot return 404 without breaking that rule
            #   410 signifies that the file is missing, without using the 404
            # I considered using 502 since this does act as a proxy to the file system
            #   And the error isn't client-side but server side (since the server lost track of the file)
            #   But 'Bad Gateway' doesn't explain anything about how the file is missing.
            # My final thoughts on the issue:
            #   Chrome displays 'It may have been moved or deleted.' on a 410 Which I feel represents the issue exactly
            #   because the file should exists; but it doesnt; so it must have been moved/delete
            #       Alternatively; it may have never existed
            raise ResponseError(HTTPStatus.GONE)
        else:
            raise  # pass along uncaught exceptions

# api REFERENCE ========================================================================================= api REFERENCE
# @route(__reference, no_end_slash=True, methods=["GET"])
# def reference_files(request: Request):
#     pass
#
#
# @route(__reference + "/(.+)", methods=["GET"])
# def reference_redirect(request: Request):
#     url = reformat_url(__reference)
#     return url, ResponseCode.SEE_OTHER, {'Location': url}
