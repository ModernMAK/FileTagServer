from http import HTTPStatus
from typing import Optional, List, Union

from fastapi.openapi.models import Response
from litespeed.error import ResponseError
from pydantic import ValidationError
from starlette import status
from starlette.responses import JSONResponse
from starlette.types import Message

from FileTagServer.API.common import parse_fields, SortQuery
from common import rest_api

# import json
# from http import HTTPStatus
# from typing import Dict, Union, Tuple
#
# from litespeed.error import ResponseError
# from pydantic import ValidationError
#
# import src.api as api
# from src import config
# from src.api.common import SortQuery, parse_fields, Util
# from src.api.file import FilesQuery, FileQuery, CreateFileQuery, FileDataQuery, FileTagQuery, DeleteFileQuery, \
#     ModifyFileQuery, SetFileQuery
# from src.rest.common import JsonResponse, serve_json
# from src.rest.routes import file, files, file_tags, files_tags, file_bytes, files_search
# from src.util.litespeedx import Response, Request
#
# RestResponse = Union[Response, Tuple[Dict, int, Dict[str, str]]]
#
# def setup_routes():
#     """
#     A Dummy Function To ensure endpoints have been loaded.
#     The endpoints must be finalized by calling .route(*args,**kwargs)
#     """
#     pass

# Files ===============================================================================================================
from FileTagServer.API.file import FileQuery, FilesQuery, CreateFileQuery
from FileTagServer.API.models import File
from FileTagServer.API import file as file_api

rest_route = "/rest"
files_route = f"{rest_route}/files"
files_tags_route = f"{files_route}/tags"
files_search_route = f"f{rest_route}/search"
file_route = f"{files_route}/{{file_id}}"


# FILES (GET) ======================================
@rest_api.get(files_route, response_model=List[File])
def get_files(sort: Optional[str] = None, fields: Optional[str] = None, tag_fields: Optional[str] = None) -> Union[
    JSONResponse, List[File]]:
    # Parse individual api arguments; data is validated at the api level
    sort = SortQuery.parse_str(sort)
    fields = parse_fields(fields)
    tag_fields = parse_fields(tag_fields)
    try:
        query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)

    # Try api call; if invalid, fetch errors from validation error and return Bad Request
    api_results = file_api.get_files(query)
    return api_results


# FILES (POST) ======================================
@rest_api.post(files_route, response_model=File, status_code=status.HTTP_201_CREATED)
def post_files(query: CreateFileQuery) -> File:
    api_result = file_api.create_file(query)
    return api_result
    # return serve_json(api_result.json(), HTTPStatus.Created, {'location': config.resolve_url(file.path(api_result.id))})


# Files Tags ==========================================================================================================
# @rest_api.get(files_tags_route)
# def get_files_tags(request: Request):
#     # Parse individual api arguments; data is validated at the api level
#     arguments: Dict[str, str] = request['GET']
#     sort = SortQuery.parse_str(arguments.get("sort"))
#     fields = parse_fields(arguments.get("fields"))
#     tag_fields = parse_fields(arguments.get("tag_fields"))
#     query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
#     # Try api call; if invalid, fetch errors from validation error and return Bad Request
#     api_results = api.file.get_files_tags(query)
#     return serve_json(Util.json(api_results))


# Files Search ========================================================================================================
# @rest_api.get(files_search_route)
# def get_files_search(request: Request) -> RestResponse:
#     def apply_get(path: str):
#         args: Dict = request['GET']
#         parts = [f"{k}={v}" for k, v in args.items()]
#         if len(parts) > 0:
#             return path + "?" + "&".join(parts)
#         return path
#
#     return b'', 301, {'Location': config.resolve_url(apply_get(files.path()))}


# File ================================================================================================================
@rest_api.get(file_route, response_model=File,
              responses={status.HTTP_410_GONE: {"model": None}, status.HTTP_409_CONFLICT: {"model": None}})
def get_file(file_id: int):
    try:
        query = FileQuery(id=file_id)
        api_result = file_api.get_file(query)
        return api_result
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:  # WE don't use 404 to avoid confusing it with an invalid endpoint
            return JSONResponse(status_code=status.HTTP_410_GONE, content=None)
        elif e.code == HTTPStatus.CONFLICT:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=None)
        else:
            return JSONResponse(status_code=int(e.code), content=None)

#
# @rest_api.delete(file_route)
# def delete_file(request: Request, id: int) -> Union[RestResponse, JsonResponse]:
#     try:
#         query = DeleteFileQuery(id=id)
#     except ValidationError as e:
#         return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
#     try:
#         success = api.file.delete_file(query)
#         if success:
#             return b'', HTTPStatus.NO_CONTENT, {}
#         else:
#             return b'', HTTPStatus.INTERNAL_SERVER_ERROR, {}
#     except ResponseError as e:
#         if e.code == 404:
#             raise ResponseError(HTTPStatus.GONE)
#         else:
#             raise
#
#
# @rest_api.patch(file_route)
# def patch_file(request: Request, id: str) -> Union[RestResponse, JsonResponse]:
#     body = request['BODY']
#     body_json = json.load(body)
#     body_json['id'] = id
#     try:
#         query = ModifyFileQuery.parse_obj(body_json)
#     except ValidationError as e:
#         return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
#     try:
#         api.file.modify_file(query)
#         return b'', HTTPStatus.NO_CONTENT, {}
#     except ResponseError as e:
#         if e.code == HTTPStatus.NOT_FOUND:
#             raise ResponseError(HTTPStatus.GONE)
#         else:
#             raise
#
#
# @rest_api.put(file_route)
# def put_file(request: Request, id: int) -> Union[RestResponse, JsonResponse]:
#     body = request['BODY']
#     body_json = json.loads(body)
#     body_json['id'] = id
#     try:
#         query = SetFileQuery.parse_obj(body_json)
#     except ValidationError as e:
#         return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
#     try:
#         success = api.file.set_file(query)
#         return b'', HTTPStatus.NO_CONTENT if success else HTTPStatus.INTERNAL_SERVER_ERROR, {}
#     except ResponseError as e:
#         if e.code == HTTPStatus.NOT_FOUND:
#             raise ResponseError(HTTPStatus.GONE)
#         else:
#             raise
#
#
# # File Tags ===========================================================================================================
# @rest_api.get(file_tags_route)
# def get_file_tags(request: Request, id: int) -> JsonResponse:
#     q = FileTagQuery(id=id)
#     try:
#         api_result = api.file.get_file_tags(q)
#         return serve_json(Util.json(api_result))
#     except ResponseError as e:
#         if e.code == HTTPStatus.NOT_FOUND:  # SEE get_file_bytes for why we do this
#             raise ResponseError(HTTPStatus.GONE)
#         else:
#             raise
#
#
# #
# # # SET
# # @route(__file_tags, no_end_slash=True, methods=["PUT"])
# # def put_file_tags(request: Request, id: str):
# #     body = request['BODY']
# #     file_json = json.loads(body)
# #
# #     required_fields = [__data_schema['tags']]
# #     opt_fields = []
# #     errors = []
# #     if validate_fields(file_json, required_fields, opt_fields, errors):
# #         return JSend.fail(errors), ResponseCode.BAD_REQUEST
# #     try:
# #         insert_args = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
# #         delete_sub = ', '.join('?' * len(file_json['tags']))
# #         delete_query = f"DELETE FROM file_tag WHERE file_tag.file_id = ? AND file_tag.tag_id NOT IN ({delete_sub});"
# #         insert_query = f"INSERT OR IGNORE INTO file_tag (file_id, tag_id) VALUES (:file_id,:tag_id);"
# #         delete_args = [id] + file_json['tags']
# #         with connect(config.db_path) as conn:
# #             conn.execute("PRAGMA foreign_keys = 1")
# #             cursor = conn.cursor()
# #             cursor.execute(delete_query, delete_args)
# #             cursor.executemany(insert_query, insert_args)
# #             conn.commit()
# #             return JSend.success(""), ResponseCode.NO_CONTENT
# #     except DatabaseError as e:
# #         return JSend.fail(e.args[0]), ResponseCode.INTERNAL_SERVER_ERROR
# #
# #
# # # REMOVE
# # @route(__file_tags, no_end_slash=True, methods=["DELETE"])
# # def delete_file_tags(request: Request, id: str):
# #     body = request['BODY']
# #     file_json = json.loads(body)
# #
# #     required_fields = [__data_schema['tags']]
# #     opt_fields = []
# #     errors = []
# #     if validate_fields(file_json, required_fields, opt_fields, errors):
# #         return JSend.fail(errors), ResponseCode.BAD_REQUEST
# #     try:
# #         file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
# #         with connect(config.db_path) as conn:
# #             conn.execute("PRAGMA foreign_keys = 1")
# #             cursor = conn.cursor()
# #             query = read_sql_file("static/sql/file_tag/delete_pair.sql")
# #             cursor.executemany(query, file_tag_pairs)
# #             conn.commit()
# #         return b'', ResponseCode.NO_CONTENT, {}
# #     except DatabaseError as e:
# #         return JSend.fail(e.args[0])
# #
# #
# # # ADD
# # @route(__file_tags, no_end_slash=True, methods=["POST"])
# # def post_file_tags(request: Request, id: str):
# #     body = request['BODY']
# #     file_json = json.loads(body)
# #
# #     required_fields = [__data_schema['tags']]
# #     opt_fields = []
# #     errors = []
# #     if validate_fields(file_json, required_fields, opt_fields, errors):
# #         return JSend.fail(errors), ResponseCode.BAD_REQUEST
# #     try:
# #         file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
# #         with connect(config.db_path) as conn:
# #             conn.execute("PRAGMA foreign_keys = 1")
# #             cursor = conn.cursor()
# #             query = read_sql_file("static/sql/file_tag/insert.sql")
# #             cursor.executemany(query, file_tag_pairs)
# #             conn.commit()
# #         return b'', ResponseCode.NO_CONTENT, {}
# #     except DatabaseError as e:
# #         return JSend.fail(e.args[0])
# #
# #
# # # This is just a merged post/delete
# # # # UPDATE
# # # @route(__file_tags, no_end_slash=True, methods=["PATCH"])
# # # def patch_file_tags(request: Request, id: str):
# # #     pass
# #
# # FILE DATA ================================================================================================= FILE DATA
# @rest_api.get(file_bytes_route)
# def get_file_data(request: Request, id: int):
#     range = request['HEADERS'].get('Range')
#     query = FileDataQuery(id=id, range=range)
#     try:
#         return api.file.get_file_bytes(query)
#     except ResponseError as e:
#         if e.code == 404:
#             # The 'least smelly' IMO response
#             # I'd prefer 404 ONLY be used when the endpoint itself does not exist
#             #   Therefore if a function in the rest api is called, it cannot return 404 without breaking that rule
#             #   410 signifies that the file is missing, without using the 404
#             # I considered using 502 since this does act as a proxy to the file system
#             #   And the error isn't client-side but server side (since the server lost track of the file)
#             #   But 'Bad Gateway' doesn't explain anything about how the file is missing.
#             # My final thoughts on the issue:
#             #   Chrome displays 'It may have been moved or deleted.' on a 410 Which I feel represents the issue exactly
#             #   because the file should exists; but it doesnt; so it must have been moved/delete
#             #       Alternatively; it may have never existed
#             raise ResponseError(HTTPStatus.GONE)
#         else:
#             raise  # pass along uncaught exceptions
#
# # api REFERENCE ========================================================================================= api REFERENCE
# # @route(__reference, no_end_slash=True, methods=["GET"])
# # def reference_files(request: Request):
# #     pass
# #
# #
# # @route(__reference + "/(.+)", methods=["GET"])
# # def reference_redirect(request: Request):
# #     url = reformat_url(__reference)
# #     return url, ResponseCode.SEE_OTHER, {'Location': url}
