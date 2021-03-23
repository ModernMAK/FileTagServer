import json
from os.path import join
from typing import List, Dict, Union, Tuple, Type, Iterable
from litespeed import App, start_with_args, route

from src.rest.common import reformat_url, read_sql_file, validate_fields, populate_optional
from src.util.litespeedx import multiroute, Response, Request, JSend
from sqlite3 import connect, Row, DatabaseError
from http import HTTPStatus as ResponseCode

db_path = "local.db"
RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]


def __reformat_file_row(row: Row) -> Dict:
    tag_list: List[str] = [] if row['tags'] is None else row['tags'].split()
    tags = []
    for tag in tag_list:
        tags.append({
            'id': tag,
            "url": reformat_url(f"api/tags/{tag}")
        })
    return {
        'id': row['id'],
        'url': reformat_url(f"api/files/{row['id']}"),
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
__files = "api/files"
__file = "api/files/(\d*)"
__file_alt = "api/files/:id:"
__file_tags = "api/files/(\d*)/tags"
__file_tags_alt = "api/files/:id:/tags"
__reference = "api-ref/files"


# fields (name, type, type as word, default)
def __data_schema_helper(name: str, description: str, types: Iterable[type], word_type: str, read_only: bool = False):
    return {'name': name, 'description': description, 'types': types, 'type_description': word_type,
            'read_only': read_only}


__data_schema = {
    'id': __data_schema_helper('id', "Id of the file", [int], "integer", True),
    'name': __data_schema_helper('name', "Name of the file", [str], "string", False),
    'path': __data_schema_helper('path', "Path/URI to the file", [str], "string", False),
    'mime': __data_schema_helper('mime', "Mime-type of the file", [str], "string", False),
    'description': __data_schema_helper('description', "Description of the file", [str], "string", False),
    'tags': __data_schema_helper('tags', "List of tags for the file", [List[int]], "list of integers", True)
}

__func_schema = {
    __files: {'name': __file, 'methods': {
        "GET": {"description": "Retrieves a list"}
    }}
}


@route(__files, no_end_slash=True, methods="GET")
def get_files(request: Request) -> Dict:
    with connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = Row
        query = read_sql_file("static/sql/file/select.sql")
        cursor.execute(query)
        rows = cursor.fetchall()
        formatted = []
        for row in rows:
            formatted.append(__reformat_file_row(row))
        return JSend.success(formatted)


@route(__file, no_end_slash=True, methods="GET")
def get_file(request: Request, id: str) -> RestResponse:
    with connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = Row
        query = read_sql_file("static/sql/file/select_by_id.sql")
        cursor.execute(query, id)
        rows = cursor.fetchall()
        if len(rows) < 1:
            return JSend.fail(f"No file found with the given id: '{id}'"), ResponseCode.NOT_FOUND
        elif len(rows) > 1:
            return JSend.fail(f"Too many files found with the given id: '{id}'"), ResponseCode.CONFLICT
        return JSend.success(__reformat_file_row(rows[0]))


@route(__file, no_end_slash=True, methods="DELETE")
def delete_file(request: Request, id: str) -> Dict:
    try:
        with connect(db_path) as conn:
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file/delete_by_id.sql")
            cursor.execute(query, id)
            conn.commit()
        return JSend.success(f"Deleted file '{id}'")
    except DatabaseError as e:
        return JSend.fail(e)


@route(__file, no_end_slash=True, methods="PATCH")
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
        with connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, file_json)
            conn.commit()
        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e)


@route(__file, no_end_slash=True, methods="PUT")
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
        with connect(db_path) as conn:
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file/update.sql")
            cursor.execute(query, file_json)
            conn.commit()

        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e)


@route(__file, no_end_slash=True, methods="POST")
def post_file(request: Request) -> RestResponse:
    body = request['BODY']
    file_json = json.loads(body)
    errors = []
    req_fields = [__data_schema['path']]
    opt_fields = [__data_schema['name'], __data_schema['mime'], __data_schema['description']]
    validate_fields(file_json, req_fields, opt_fields, errors)
    populate_optional(file_json, opt_fields)

    if len(errors) > 0:
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        with connect(db_path) as conn:
            cursor = conn.cursor()
            query = read_sql_file("static/sql/file/insert.sql")
            cursor.execute(query, file_json)
            conn.commit()
            id = cursor.lastrowid
            file = {
                'id': id,
                'url': reformat_url(f"api/files/{id}"),
            }
        return JSend.success(file), ResponseCode.CREATED, {'Location': file['url']}
    except DatabaseError as e:
        return JSend.fail(e)


@route(__file_tags, no_end_slash=True, methods="GET")
def get_file_tags(request: Request, id: str) -> RestResponse:
    with connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = Row

        file_query = read_sql_file("static/sql/file/select_by_id.sql")
        cursor.execute(file_query, id)
        files = cursor.fetchall()
        if len(files) < 1:
            return JSend.fail(f"No file found with the given id: '{id}'"), ResponseCode.NOT_FOUND
        elif len(files) > 1:
            return JSend.fail(f"Too many files found with the given id: '{id}'"), ResponseCode.CONFLICT

        tag_id_list: List[str] = [] if files[0]['tags'] is None else files[0]['tags'].split()

        internal_tag_query = read_sql_file("static/sql/tag/select.sql", True)
        tag_query = f"SELECT * FROM ({internal_tag_query}) WHERE tag.id IN ({'?' * len(tag_id_list)}) "
        cursor.execute(tag_query, tag_id_list)
        tags = cursor.fetchall()
        formatted = []
        for tag in tags:
            formatted.append(__reformat_tag_row(tag))
        return JSend.success(formatted)


# READ
@route(__file_tags, no_end_slash=True, methods="GET")
def patch_file_tags(request: Request):
    pass


# SET
@route(__file_tags, no_end_slash=True, methods="PUT")
def put_file_tags(request: Request):
    pass


# REMOVE
@route(__file_tags, no_end_slash=True, methods="DELETE")
def delete_file_tags(request: Request):
    pass


# ADD
@route(__file_tags, no_end_slash=True, methods="POST")
def post_file_tags(request: Request):
    pass


# UPDATE
@route(__file_tags, no_end_slash=True, methods="PATCH")
def patch_file_tags(request: Request):
    pass


# API REFERENCE ========================================================================================= API REFERENCE

@route(__reference, no_end_slash=True, methods="GET")
def reference_files(request: Request):
    return {'data': __data_schema, 'func': __func_schema}


@route(__reference + "/(.+)", methods="GET")
def reference_redirect(request: Request):
    url = reformat_url(__reference)
    return url, ResponseCode.SEE_OTHER, {'Location': url}


if __name__ == "__main__":
    @route()
    def index(request: Request):
        return reference_redirect(request)


    start_with_args()
