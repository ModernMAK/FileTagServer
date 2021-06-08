from http import HTTPStatus
from typing import Optional, List

from fastapi import Header
# from litespeed.error import ResponseError
from pydantic import ValidationError
from starlette import status
from starlette.responses import JSONResponse, FileResponse

from FileTagServer.API import file as file_api
from FileTagServer.API.common import parse_fields, SortQuery
# Files ===============================================================================================================
from FileTagServer.API.error import ApiError
from FileTagServer.API.file import FileQuery, FilesQuery, CreateFileQuery, DeleteFileQuery, ModifyFileQuery, \
    FullModifyFileQuery, SetFileQuery, FullSetFileQuery, FileTagQuery, FileDataQuery
from FileTagServer.API.models import File, Tag
from common import rest_api

tags_metadata = [
    {"name": "Files", "description": ""},
    {"name": "File", "description": ""},
]

rest_route = "/rest"
files_route = f"{rest_route}/files"
files_tags_route = f"{files_route}/tags"
files_search_route = f"f{rest_route}/search"
file_route = f"{files_route}/{{file_id}}"
file_tags_route = f"{file_route}/tags"
file_bytes_route = f"{file_route}/bytes"


# FILES (GET) ======================================
@rest_api.get(files_route, response_model=List[File], tags=["Files"])
def get_files(sort: Optional[str] = None, fields: Optional[str] = None, tag_fields: Optional[str] = None) -> List[File]:
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
@rest_api.post(files_route, name="Create File", description="Creates a new File", response_model=File,
               status_code=status.HTTP_201_CREATED,
               tags=["Files"])
def post_files(query: CreateFileQuery) -> File:
    api_result = file_api.create_file(query)
    return api_result
    # return serve_json(api_result.json(), HTTPStatus.Created, {'location': config.resolve_url(file.path(api_result.id))})


# FILES TAGS (GET) ==========================================================================================================
@rest_api.get(files_tags_route, response_model=List[Tag], tags=["Files", "Tag"])
def get_files_tags(sort: Optional[str] = None, fields: Optional[str] = None, tag_fields: Optional[str] = None) -> List[
    Tag]:
    sort = SortQuery.parse_str(sort)
    fields = parse_fields(fields)
    tag_fields = parse_fields(tag_fields)
    query = FilesQuery(sort=sort, fields=fields, tag_fields=tag_fields)
    api_results = file_api.get_files_tags(query)
    return api_results


# # FILES SEARCH (GET) ========================================================================================================
# @rest_api.get(files_search_route)
# def get_files_search() -> RedirectResponse:
#     def apply_get(path: str):
#         args: Dict = request['GET']
#         parts = [f"{k}={v}" for k, v in args.items()]
#         if len(parts) > 0:
#             return path + "?" + "&".join(parts)
#         return path
#
#     return RedirectResponse(url=config.resolve_url(apply_get(files_route)),
#                             status_code=status.HTTP_301_MOVED_PERMANENTLY)


# FILE (GET) ================================================================================================================
@rest_api.get(file_route, response_model=File,
              responses={status.HTTP_410_GONE: {"model": None}, status.HTTP_409_CONFLICT: {"model": None}},
              tags=["File"])
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
@rest_api.delete(file_route, status_code=status.HTTP_204_NO_CONTENT, responses={status.HTTP_410_GONE: {'model': None}},
                 tags=["File"])
def delete_file(file_id: int):
    try:
        query = DeleteFileQuery(id=file_id)
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    try:
        file_api.delete_file(query)
        return None
    except ResponseError as e:
        if e.code == 404:
            return JSONResponse(status_code=status.HTTP_410_GONE)


@rest_api.patch(file_route, status_code=status.HTTP_204_NO_CONTENT, tags=["File"])
def patch_file(file_id: int, body: ModifyFileQuery):
    try:
        query = FullModifyFileQuery(id=file_id, **body.dict())
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
    try:
        file_api.modify_file(query)
        return
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:
            return JSONResponse(status_code=status.HTTP_410_GONE)
        else:
            return JSONResponse(status_code=int(e.code))


#
#
@rest_api.put(file_route, status_code=status.HTTP_204_NO_CONTENT, tags=["File"])
def put_file(file_id: int, body: SetFileQuery):
    try:
        query = FullSetFileQuery(id=file_id, **body.dict())
    except ValidationError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST)
        # return serve_json(e.json(), HTTPStatus.BAD_REQUEST)
    try:
        # success = \
        file_api.set_file(query)
        return
        # return b'', HTTPStatus.NO_CONTENT if success else HTTPStatus.INTERNAL_SERVER_ERROR, {}
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:
            return JSONResponse(status_code=status.HTTP_410_GONE)
        else:
            return JSONResponse(status_code=int(e.code))
            # raise


#
#
# # File Tags ===========================================================================================================
@rest_api.get(file_tags_route, tags=["File", "Tag"])
def get_file_tags(file_id: int) -> List[Tag]:
    q = FileTagQuery(id=file_id)
    try:
        api_result = file_api.get_file_tags(q)
        return api_result
        # return serve_json(Util.json(api_result))
    except ResponseError as e:
        if e.code == HTTPStatus.NOT_FOUND:  # SEE get_file_bytes for why we do this
            return JSONResponse(status_code=status.HTTP_410_GONE)
            # raise ResponseError(HTTPStatus.GONE)
        else:
            return JSONResponse(status_code=int(e.code))
            # raise


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
# FILE DATA ================================================================================================= FILE DATA
@rest_api.get(file_bytes_route, tags=["File"], response_class=FileResponse)
def get_file_data(file_id: int, range: Optional[str] = Header(None)):
    # range = request['HEADERS'].get('Range')
    # query = FileDataQuery(id=file_id, range=range)
    try:
        local_path = file_api.get_file_path(file_id)
        return FileResponse(path=local_path, headers={'range': range})
    except ApiError as e:
        return JSONResponse(status_code=e.status_code, content={'message': e.message})
        # if e.code == 404:
        #     return JSONResponse(status_code=status.HTTP_410_GONE)
        #     # The 'least smelly' IMO response
        #     # I'd prefer 404 ONLY be used when the endpoint itself does not exist
        #     #   Therefore if a function in the rest api is called, it cannot return 404 without breaking that rule
        #     #   410 signifies that the file is missing, without using the 404
        #     # I considered using 502 since this does act as a proxy to the file system
        #     #   And the error isn't client-side but server side (since the server lost track of the file)
        #     #   But 'Bad Gateway' doesn't explain anything about how the file is missing.
        #     # My final thoughts on the issue:
        #     #   Chrome displays 'It may have been moved or deleted.' on a 410 Which I feel represents the issue exactly
        #     #   because the file should exists; but it doesnt; so it must have been moved/delete
        #     #       Alternatively; it may have never existed
        #     # raise ResponseError(HTTPStatus.GONE)
        # else:
        #     return JSONResponse(status_code=int(e.code))
        #     # raise  # pass along uncaught exceptions
