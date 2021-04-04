import json
from typing import List, Dict, Union, Tuple, Type, Iterable
from litespeed import App, start_with_args, route, serve
from litespeed.error import ResponseError

from src import config
from src.api.common import parse_sort_query
from src.api.file import ValidationError
from src.rest.common import reformat_url, read_sql_file, validate_fields, populate_optional
import src.rest.common as rest
from src.util.litespeedx import Response, Request, JSend
from sqlite3 import connect, Row, DatabaseError
from http import HTTPStatus as ResponseCode
import src.api as api

RestResponse = Union[Response, Tuple[Dict, int, Dict[str, str]]]


def __reformat_file_row(row: Row) -> Dict:
    tag_list: List[str] = [] if row['tags'] is None else row['tags'].split(",")
    tags = []
    for tag in tag_list:
        tags.append({
            'id': tag,
            "url": reformat_url(f"api/tags/{tag}")
        })
    return {
        'id': row['id'],
        'urls': {
            "self": reformat_url(f"{__files}/{row['id']}"),
            "tags": reformat_url(f"{__files}/{row['id']}/tags"),
            "data": reformat_url(f"{__files}/{row['id']}/data"),
        },
        'internal_path': row['path'],
        'mime': row['mime'],
        'name': row['name'],
        'description': row['description'],
        'tags': tags
    }


def __reformat_tag_row(row: Row) -> Dict:
    return {
        'id': row['id'],
        'url': reformat_url(f"api/tags/{row['id']}"),
        'name': row['name'],
        'description': row['description'],
        'count': row['count'],
    }


# shared urls
__files = r"api/files"
__files_search = r"api/files/search"
__files_tags = r"api/files/tags"
__file = r"api/files/(\d*)"
__file_tags = r"api/files/(\d*)/tags"
__file_data = r"api/files/(\d*)/data"
__reference = r"api-ref/files"


def __file_alt(id: int):
    return fr"api/files/{id}"


def __file_tags_alt(id: int):
    return fr"api/files/{id}/tags"


def __file_data_alt(id: int):
    return fr"api/files/{id}/data"


# fields (name, type, type as word, default)
def __data_schema_helper(name: str, description: str, types: Iterable[type], word_type: str, read_only: bool = False):
    return {'name': name, 'description': description, 'types': types, 'type_description': word_type,
            'read_only': read_only}


__data_schema = {
    'id': __data_schema_helper('id', "Id of the file", (int,), "integer", True),
    'name': __data_schema_helper('name', "Name of the file", (str,), "string", False),
    'path': __data_schema_helper('path', "Path/URI to the file", (str,), "string", False),
    'mime': __data_schema_helper('mime', "Mime-type of the file", (str,), "string", False),
    'description': __data_schema_helper('description', "Description of the file", (str,), "string", False),
    'tags': __data_schema_helper('tags', "List of tags for the file", (list,), "list of integers", True)
}

__func_schema = {
    __files: {'name': __file, 'methods': {
        "GET": {"description": "Retrieves a list"}
    }}
}


# SQL

# Files ===============================================================================================================
@route(url=__files, no_end_slash=True, methods=["GET"])
def get_files(request: Request) -> RestResponse:
    # Parse individual api arguments; data is validated at the api level
    arguments: Dict[str, str] = request['GET']
    sort_args = parse_sort_query(arguments.get("sort"))
    # Try api call; if invalid, fetch errors from validation error and return Bad Request
    try:
        rows = api.file.get_files(sort_args)
        formatted = []
        for row in rows:
            formatted.append(__reformat_file_row(row))
        return JSend.success(formatted), ResponseCode.OK, {}
    except ValidationError as e:
        return JSend.fail(e.errors), ResponseCode.BAD_REQUEST, {}

@property
@route(url=__files, no_end_slash=True, methods=["POST"])
def post_files(request: Request) -> RestResponse:
    header: Dict[str, str] = request['HEADERS']
    body: str = request['BODY']
    body_as_json = json.loads(body)
    use_batch = header.get(rest.Batch_Request_Header, False)
    try:
        use_batch = bool(use_batch)
    except TypeError:
        errors = [f'Batch Request Header was present, but invalid: \'{use_batch}\', expected \'true\' or \'false\'.']
        return JSend.fail(errors), ResponseCode.BAD_REQUEST, {}

    def handle_batch(body_json: dict):
        data = []
        for single_body in body_json:
            result, code, headers = handle_single(single_body)
            data.append({'result': result, 'code': code, 'headers': headers})
        return JSend.success(data), ResponseCode.OK,

    def handle_single(body_json: dict):
        body_json = json.loads(body)
        errors = []
        req_fields = [__data_schema['path']]
        opt_fields = [__data_schema['name'], __data_schema['mime'], __data_schema['description']]
        validate_fields(body_json, req_fields, opt_fields, errors)
        populate_optional(body_json, opt_fields)

        if len(errors) > 0:
            return JSend.fail(errors), ResponseCode.BAD_REQUEST
        try:
            with connect(config.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = 1")
                cursor = conn.cursor()
                query = read_sql_file("static/sql/file/insert.sql")
                cursor.execute(query, body_json)
                conn.commit()
                id = cursor.lastrowid
                file = {
                    'id': id,
                    'url': reformat_url(f"api/files/{id}"),
                }
            return JSend.success(file), ResponseCode.CREATED, {'Location': file['url']}
        except DatabaseError as e:
            return JSend.fail(e.args[0])

    if use_batch:
        return handle_batch(body_as_json)
    else:
        return handle_single(body_as_json)


# Files Tags ==========================================================================================================
@route(url=__files_tags, no_end_slash=True, methods=["GET"])
def get_files_tags(request: Request) -> RestResponse:
    # Parse individual api arguments; data is validated at the api level
    arguments: Dict[str, str] = request['GET']
    sort_args = parse_sort_query(arguments.get("sort"))
    # Try api call; if invalid, fetch errors from validation error and return Bad Request
    try:
        rows = api.file.get_files_tags(sort_args)
        formatted = []
        for row in rows:
            formatted.append(__reformat_tag_row(row))
        return JSend.success(formatted), ResponseCode.OK
    except ValidationError as e:
        return JSend.fail(e.errors), ResponseCode.BAD_REQUEST


# Files Search ========================================================================================================
@route(url=__files_search, no_end_slash=True, methods=["GET"])
def get_files_search(request: Request) -> RestResponse:
    def apply_get(path: str):
        args: Dict = request['GET']
        parts = [f"{k}={v}" for k, v in args.items()]
        if len(parts) > 0:
            return path + "?" + "&".join(parts)
        return path

    return b'', 301, {'Location': apply_get(reformat_url(__files))}


# File ================================================================================================================
def __get_single_file_internal(cursor, id: str) -> Row:
    query = read_sql_file("static/sql/file/select_by_id.sql")
    cursor.execute(query, id)
    rows = cursor.fetchall()
    if len(rows) < 1:
        raise ResponseError(ResponseCode.NOT_FOUND, f"No file found with the given id: '{id}'")
    elif len(rows) > 1:
        raise ResponseError(ResponseCode.MULTIPLE_CHOICES, f"Too many files found with the given id: '{id}'")
    return rows[0]


@route(__file, no_end_slash=True, methods=["GET"])
def get_file(request: Request, id: str) -> RestResponse:
    with connect(config.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        cursor.row_factory = Row
        try:
            result = __get_single_file_internal(cursor, id)
            result = __reformat_file_row(result)
            return JSend.success(result)
        except ResponseError as e:
            return JSend.fail(e.message), e.code


@route(__file, no_end_slash=True, methods=["DELETE"])
def delete_file(request: Request, id: str) -> RestResponse:
    try:
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file/delete_by_id.sql")
            cursor.execute(query, id)
            conn.commit()
        return b'', ResponseCode.NO_CONTENT, {}  # , JSend.success(f"Deleted file '{id}'")
    except DatabaseError as e:
        return JSend.fail(e.args[0])


@route(__file, no_end_slash=True, methods=["PATCH"])
def patch_file(request: Request, id: str) -> RestResponse:
    body = request['BODY']
    file_json = json.loads(body)

    required_fields = []
    optional_fields = [__data_schema['name'], __data_schema['mime'], __data_schema['description'],
                       __data_schema['path']]

    errors = []

    if validate_fields(file_json, required_fields, optional_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        parts: List[str] = [f"{key} = :{key}" for key in file_json]
        query = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"

        file_json['id'] = id
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            cursor.execute(query, file_json)
            conn.commit()
        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e.args[0])


@route(__file, no_end_slash=True, methods=["PUT"])
def put_file(request: Request, id: str) -> RestResponse:
    body = request['BODY']
    file_json = json.loads(body)

    required_fields = [__data_schema['name'], __data_schema['path'], __data_schema['mime'],
                       __data_schema['description']]
    opt_fields = []
    errors = []

    if validate_fields(file_json, required_fields, opt_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        file_json['id'] = id
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file/update.sql")
            cursor.execute(query, file_json)
            conn.commit()

        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.error(e.args[0]), ResponseCode.INTERNAL_SERVER_ERROR


# File Tags ===========================================================================================================
# READ
@route(__file_tags, no_end_slash=True, methods=["GET"])
def get_file_tags(request: Request, id: str) -> RestResponse:
    with connect(config.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        cursor.row_factory = Row
        try:
            result = __get_single_file_internal(cursor, id)
        except ResponseError as e:
            return JSend.fail(e.message), e.code
        tag_id_list: List[str] = [] if result['tags'] is None else result['tags'].split()

        internal_tag_query = read_sql_file("static/sql/tag/select.sql", True)
        sub = ', '.join('?' * len(tag_id_list))
        tag_query = f"SELECT * FROM ({internal_tag_query}) WHERE id IN ({sub}) "
        cursor.execute(tag_query, tag_id_list)
        tags = cursor.fetchall()
        formatted = []
        for tag in tags:
            formatted.append(__reformat_tag_row(tag))
        return JSend.success(formatted)


# SET
@route(__file_tags, no_end_slash=True, methods=["PUT"])
def put_file_tags(request: Request, id: str):
    body = request['BODY']
    file_json = json.loads(body)

    required_fields = [__data_schema['tags']]
    opt_fields = []
    errors = []
    if validate_fields(file_json, required_fields, opt_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        insert_args = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
        delete_sub = ', '.join('?' * len(file_json['tags']))
        delete_query = f"DELETE FROM file_tag WHERE file_tag.file_id = ? AND file_tag.tag_id NOT IN ({delete_sub});"
        insert_query = f"INSERT OR IGNORE INTO file_tag (file_id, tag_id) VALUES (:file_id,:tag_id);"
        delete_args = [id] + file_json['tags']
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            cursor.execute(delete_query, delete_args)
            cursor.executemany(insert_query, insert_args)
            conn.commit()
            return JSend.success(""), ResponseCode.NO_CONTENT
    except DatabaseError as e:
        return JSend.fail(e.args[0]), ResponseCode.INTERNAL_SERVER_ERROR


# REMOVE
@route(__file_tags, no_end_slash=True, methods=["DELETE"])
def delete_file_tags(request: Request, id: str):
    body = request['BODY']
    file_json = json.loads(body)

    required_fields = [__data_schema['tags']]
    opt_fields = []
    errors = []
    if validate_fields(file_json, required_fields, opt_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file_tag/delete_pair.sql")
            cursor.executemany(query, file_tag_pairs)
            conn.commit()
        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e.args[0])


# ADD
@route(__file_tags, no_end_slash=True, methods=["POST"])
def post_file_tags(request: Request, id: str):
    body = request['BODY']
    file_json = json.loads(body)

    required_fields = [__data_schema['tags']]
    opt_fields = []
    errors = []
    if validate_fields(file_json, required_fields, opt_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        file_tag_pairs = [{'file_id': id, 'tag_id': tag} for tag in file_json['tags']]
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file_tag/insert.sql")
            cursor.executemany(query, file_tag_pairs)
            conn.commit()
        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e.args[0])


# This is just a merged post/delete
# # UPDATE
# @route(__file_tags, no_end_slash=True, methods=["PATCH"])
# def patch_file_tags(request: Request, id: str):
#     pass

# FILE DATA ================================================================================================= FILE DATA
@route(__file_data, no_end_slash=True, methods=["GET"])
def get_file_data(request: Request, id: str):
    try:
        id = int(id)
        range = request['HEADERS'].get('Range')
        return api.file.get_file_data(id, range)
    except ResponseError as e:
        return JSend.fail(e.message), e.code


# api REFERENCE ========================================================================================= api REFERENCE
@route(__reference, no_end_slash=True, methods=["GET"])
def reference_files(request: Request):
    pass


@route(__reference + "/(.+)", methods=["GET"])
def reference_redirect(request: Request):
    url = reformat_url(__reference)
    return url, ResponseCode.SEE_OTHER, {'Location': url}
