# from http import HTTPStatus
# from typing import Optional, List, Dict, Any
#
# from requests import request
# from fastapi import Header
# from pydantic import ValidationError
# from starlette import status
# from starlette.responses import JSONResponse
# from FileTagServer.DBI import file as file_api
# from FileTagServer.DBI.common import parse_fields, SortQuery, fields_to_str
# from FileTagServer.DBI.error import ApiError
# from FileTagServer.DBI.file import FileQuery, FilesQuery, CreateFileQuery, DeleteFileQuery, ModifyFileQuery, \
#     FullModifyFileQuery, SetFileQuery, FullSetFileQuery, FileTagQuery
# from FileTagServer.DBI.models import File, Tag, RestFile
# from FileTagServer.REST.common import rest_api
# from FileTagServer.REST.routing import files_route, files_tags_route, file_route, file_tags_route, file_bytes_route, \
#     reformat
# from FileTagServer.WEB.common import serve_streamable
#
#
# def drop_none_args(args: Dict[str, Any]) -> Dict[str, Any]:
#     return {k: v for k, v in args.items() if v is not None}
#
#
# # FILES (GET) ======================================
# def get_files(url: str, sort: Optional[List[SortQuery]] = None, fields: Optional[List[str]] = None,
#               tag_fields: Optional[List[str]] = None) -> List[File]:
#     route = files_route
#     full_url = url + route
#     method = "GET"
#     args = {
#         'sort': SortQuery.list_to_str(sort),
#         'fields': fields_to_str(fields),
#         'tag_fields': fields_to_str(tag_fields)
#     }
#     args = drop_none_args(args)
#     response = request(method, full_url, params=args)
#     if response.status_code == status.HTTP_200_OK:
#         json = response.json()
#         files = [File.parse_obj(data) for data in json]
#         return files
#     else:
#         raise ApiError(status_code=response.status_code, message=response.json())
#
#
# def get_file(url: str, file_id: int, fields: Optional[List[str]] = None,
#              tag_fields: Optional[List[str]] = None) -> File:
#     route = file_route
#     full_url = url + route
#     method = "GET"
#     args = {
#         'fields': fields_to_str(fields),
#         'tag_fields': fields_to_str(tag_fields)
#     }
#     drop_none_args(args)
#     full_url = reformat(full_url, file_id=file_id)
#     response = request(method, full_url, params=args)
#     if response.status_code == status.HTTP_200_OK:
#         json = response.json()
#         set_fields = None if not fields else set(fields)
#         file = RestFile.construct(set_fields, **json).copy(include=set_fields)
#         return file
#     else:
#         try:
#             raise ApiError(status_code=response.status_code, message=response.json())
#         except ValueError:
#             raise ApiError(status_code=response.status_code, message=response.raw)
#
#
# # FILES (POST) ======================================
# @rest_api.post(files_route, name="Create File", description="Creates a new File", response_model=File,
#                status_code=status.HTTP_201_CREATED,
#                tags=["Files"])
# def post_files(query: CreateFileQuery) -> File:
#     api_result = file_api.create_file(query)
#     return api_result
#     # return serve_json(api_result.json(), HTTPStatus.Created, {'location': config.resolve_url(file.path(api_result.id))})
#
#
# # FILES TAGS (GET) ==========================================================================================================
# @rest_api.get(files_tags_route, response_model=List[Tag], tags=["Files", "Tag"])
# def get_files_tags(sort: Optional[str] = None, fields: Optional[str] = None, tag_fields: Optional[str] = None) -> List[
#     Tag]:
#     sort = SortQuery.parse_str(sort)
#     fields = parse_fields(fields)
#     tag_fields = parse_fields(tag_fields)
#     query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
#     api_results = file_api.get_files_tags(query)
#     return api_results
#
#
# # # FILES SEARCH (GET) ========================================================================================================
# # @rest_api.get(files_search_route)
# # def get_files_search() -> RedirectResponse:
# #     def apply_get(path: str):
# #         args: Dict = request['GET']
# #         parts = [f"{k}={v}" for k, v in args.items()]
# #         if len(parts) > 0:
# #             return path + "?" + "&".join(parts)
# #         return path
# #
# #     return RedirectResponse(url=config.resolve_url(apply_get(files_route)),
# #                             status_code=status.HTTP_301_MOVED_PERMANENTLY)
#
#
# #
# @rest_api.delete(file_route, status_code=status.HTTP_204_NO_CONTENT, responses={status.HTTP_410_GONE: {'model': None}},
#                  tags=["File"])
# def delete_file(file_id: int):
#     try:
#         query = DeleteFileQuery(id=file_id)
#     except ValidationError as e:
#         return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
#     try:
#         file_api.delete_file(query)
#         return None
#     except ApiError as e:
#         # if e.code == 404:
#         return JSONResponse(status_code=int(e.status_code))
#
#
# @rest_api.patch(file_route, status_code=status.HTTP_204_NO_CONTENT, tags=["File"])
# def patch_file(file_id: int, body: ModifyFileQuery):
#     try:
#         query = FullModifyFileQuery(id=file_id, **body.dict())
#     except ValidationError as e:
#         return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
#     try:
#         file_api.modify_file(query)
#         return
#     except ApiError as e:
#         if e.status_code == HTTPStatus.NOT_FOUND:
#             return JSONResponse(status_code=status.HTTP_410_GONE)
#         else:
#             return JSONResponse(status_code=int(e.status_code))
#
#
# #
# #
# @rest_api.put(file_route, status_code=status.HTTP_204_NO_CONTENT, tags=["File"])
# def put_file(file_id: int, body: SetFileQuery):
#     try:
#         query = FullSetFileQuery(id=file_id, **body.dict())
#     except ValidationError as e:
#         return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
#         # return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
#     try:
#         # success = \
#         file_api.set_file(query)
#         return
#         # return b'', HTTPStatus.NO_CONTENT if success else HTTPStatus.INTERNAL_SERVER_ERROR, {}
#     except ApiError as e:
#         if e.status_code == HTTPStatus.NOT_FOUND:
#             return JSONResponse(status_code=status.HTTP_410_GONE)
#         else:
#             return JSONResponse(status_code=int(e.status_code))
#             # raise
#
#
# #
# #
# # # File Tags ===========================================================================================================
# @rest_api.get(file_tags_route, tags=["File", "Tag"])
# def get_file_tags(file_id: int) -> List[Tag]:
#     q = FileTagQuery(id=file_id)
#     try:
#         api_result = file_api.get_file_tags(q)
#         return api_result
#         # return serve_json(Util.json(api_result))
#     except ApiError as e:
#         if e.status_code == HTTPStatus.NOT_FOUND:  # SEE get_file_bytes for why we do this
#             return JSONResponse(status_code=status.HTTP_410_GONE)
#             # raise ResponseError(HTTPStatus.GONE)
#         else:
#             return JSONResponse(status_code=int(e.status_code))
#             # raise
#
#
# #
# #
# # #
# # # # SET
# # # @route(__file_tags, no_end_slash=True, methods=["PUT"])
# # # def put_file_tags(request: Request, id: str):
# # #     body = request['BODY']
# # #     file_json = json.loads(body)
# # #
# # #     required_fields = [__data_schema['tags']]
# # #     opt_fields = []
# # #     errors = []
# # #     if validate_fields(file_json, required_fields, opt_fields, errors):
# # #         return JSend.fail(errors), ResponseCode.BAD_REQUEST
# # #     try:
# # #         insert_args = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
# # #         delete_sub = ', '.join('?' * len(file_json['tags']))
# # #         delete_query = f"DELETE FROM file_tag WHERE file_tag.file_id = ? AND file_tag.tag_id NOT IN ({delete_sub});"
# # #         insert_query = f"INSERT OR IGNORE INTO file_tag (file_id, tag_id) VALUES (:file_id,:tag_id);"
# # #         delete_args = [id] + file_json['tags']
# # #         with connect(config.db_path) as conn:
# # #             conn.execute("PRAGMA foreign_keys = 1")
# # #             cursor = conn.cursor()
# # #             cursor.execute(delete_query, delete_args)
# # #             cursor.executemany(insert_query, insert_args)
# # #             conn.commit()
# # #             return JSend.success(""), ResponseCode.NO_CONTENT
# # #     except DatabaseError as e:
# # #         return JSend.fail(e.args[0]), ResponseCode.INTERNAL_SERVER_ERROR
# # #
# # #
# # # # REMOVE
# # # @route(__file_tags, no_end_slash=True, methods=["DELETE"])
# # # def delete_file_tags(request: Request, id: str):
# # #     body = request['BODY']
# # #     file_json = json.loads(body)
# # #
# # #     required_fields = [__data_schema['tags']]
# # #     opt_fields = []
# # #     errors = []
# # #     if validate_fields(file_json, required_fields, opt_fields, errors):
# # #         return JSend.fail(errors), ResponseCode.BAD_REQUEST
# # #     try:
# # #         file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
# # #         with connect(config.db_path) as conn:
# # #             conn.execute("PRAGMA foreign_keys = 1")
# # #             cursor = conn.cursor()
# # #             query = read_sql_file("static/sql/file_tag/delete_pair.sql")
# # #             cursor.executemany(query, file_tag_pairs)
# # #             conn.commit()
# # #         return b'', ResponseCode.NO_CONTENT, {}
# # #     except DatabaseError as e:
# # #         return JSend.fail(e.args[0])
# # #
# # #
# # # # ADD
# # # @route(__file_tags, no_end_slash=True, methods=["POST"])
# # # def post_file_tags(request: Request, id: str):
# # #     body = request['BODY']
# # #     file_json = json.loads(body)
# # #
# # #     required_fields = [__data_schema['tags']]
# # #     opt_fields = []
# # #     errors = []
# # #     if validate_fields(file_json, required_fields, opt_fields, errors):
# # #         return JSend.fail(errors), ResponseCode.BAD_REQUEST
# # #     try:
# # #         file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
# # #         with connect(config.db_path) as conn:
# # #             conn.execute("PRAGMA foreign_keys = 1")
# # #             cursor = conn.cursor()
# # #             query = read_sql_file("static/sql/file_tag/insert.sql")
# # #             cursor.executemany(query, file_tag_pairs)
# # #             conn.commit()
# # #         return b'', ResponseCode.NO_CONTENT, {}
# # #     except DatabaseError as e:
# # #         return JSend.fail(e.args[0])
# # #
# # #
# # # # This is just a merged post/delete
# # # # # UPDATE
# # # # @route(__file_tags, no_end_slash=True, methods=["PATCH"])
# # # # def patch_file_tags(request: Request, id: str):
# # # #     pass
# # #
# # FILE DATA ================================================================================================= FILE DATA
# @rest_api.get(file_bytes_route, tags=["File"], response_class=RestFile)
# def get_file_data(file_id: int, range: Optional[str] = Header(None)):
#     # range = request['HEADERS'].get('Range')
#     # query = FileDataQuery(id=file_id, range=range)
#     try:
#         local_path = file_api.get_file_path(file_id)
#         return serve_streamable(local_path,range)
#     except ApiError as e:
#         return JSONResponse(status_code=e.status_code, content={'message': e.message})
#         # if e.code == 404:
#         #     return JSONResponse(status_code=status.HTTP_410_GONE)
#         #     # The 'least smelly' IMO response
#         #     # I'd prefer 404 ONLY be used when the endpoint itself does not exist
#         #     #   Therefore if a function in the rest api is called, it cannot return 404 without breaking that rule
#         #     #   410 signifies that the file is missing, without using the 404
#         #     # I considered using 502 since this does act as a proxy to the file system
#         #     #   And the error isn't client-side but server side (since the server lost track of the file)
#         #     #   But 'Bad Gateway' doesn't explain anything about how the file is missing.
#         #     # My final thoughts on the issue:
#         #     #   Chrome displays 'It may have been moved or deleted.' on a 410 Which I feel represents the issue exactly
#         #     #   because the file should exists; but it doesnt; so it must have been moved/delete
#         #     #       Alternatively; it may have never existed
#         #     # raise ResponseError(HTTPStatus.GONE)
#         # else:
#         #     return JSONResponse(status_code=int(e.code))
#         #     # raise  # pass along uncaught exceptions
