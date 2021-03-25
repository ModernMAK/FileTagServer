import json
from os.path import join
from typing import List, Dict, Union, Tuple, Type, Iterable
from litespeed import App, start_with_args, route
from litespeed.error import ResponseError

from src import config
from src.rest.common import reformat_url, read_sql_file, validate_fields, populate_optional
import src.rest.common as rest
from src.util.litespeedx import Response, Request, JSend
from sqlite3 import connect, Row, DatabaseError
from http import HTTPStatus as ResponseCode

RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]


def __reformat_tag_row(row: Row) -> Dict:
    return {
        'id': row['id'],
        'url': reformat_url(f"api/tags/{row['id']}"),
        'name': row['name'],
        'description': row['description'],
        'count': row['count'],
    }


# shared urls
__tags = r"api/tags"
__tag = r"api/tags/(\d*)"


# fields (name, type, type as word, default)
def __data_schema_helper(name: str, description: str, types: Tuple, word_type: str, read_only: bool = False):
    return {'name': name, 'description': description, 'types': types, 'type_description': word_type,
            'read_only': read_only}


__data_schema = {
    'id': __data_schema_helper('id', "Id of the tag", (int,), "integer", True),
    'name': __data_schema_helper('name', "Name of the tag", (str,), "string", False),
    'description': __data_schema_helper('description', "Description of the tag", (str,), "string", False)
}


#
# __func_schema = {
#     __files: {'name': __file, 'methods': {
#         "GET": {"description": "Retrieves a list"}
#     }}
# }


# Tags ===============================================================================================================
@route(url=__tags, no_end_slash=True, methods=["GET"])
def get_tags(request: Request) -> Dict:
    with connect(config.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        cursor.row_factory = Row
        query = read_sql_file("static/sql/tag/select.sql")
        cursor.execute(query)
        rows = cursor.fetchall()
        formatted = []
        for row in rows:
            formatted.append(__reformat_tag_row(row))
        return JSend.success(formatted)


@route(url=__tags, no_end_slash=True, methods=["POST"])
def post_tags(request: Request) -> RestResponse:
    body = request['BODY']
    file_json = json.loads(body)
    errors = []
    req_fields = [__data_schema['name']]
    opt_fields = [__data_schema['description']]
    validate_fields(file_json, req_fields, opt_fields, errors)
    populate_optional(file_json, opt_fields)

    if len(errors) > 0:
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/tag/insert.sql")
            cursor.execute(query, file_json)
            conn.commit()
            id = cursor.lastrowid
            tag = {
                'id': id,
                'url': reformat_url(f"api/files/{id}"),
            }
        return JSend.success(tag), ResponseCode.CREATED, {'Location': tag['url']}
    except DatabaseError as e:
        return JSend.fail(e.args[0])


# File ================================================================================================================
def __get_single_tag_internal(cursor, id: str) -> Row:
    query = read_sql_file("static/sql/tag/select_by_id.sql")
    cursor.execute(query, id)
    rows = cursor.fetchall()
    if len(rows) < 1:
        raise ResponseError(ResponseCode.NOT_FOUND, f"No tag found with the given id: '{id}'")
    elif len(rows) > 1:
        raise ResponseError(ResponseCode.MULTIPLE_CHOICES, f"Too many tags found with the given id: '{id}'")
    return rows[0]


@route(__tag, no_end_slash=True, methods=["GET"])
def get_tag(request: Request, id: str) -> RestResponse:
    with connect(config.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        cursor.row_factory = Row
        try:
            result = __get_single_tag_internal(cursor, id)
            result = __reformat_tag_row(result)
            return JSend.success(result)
        except ResponseError as e:
            return JSend.fail(e.message), e.code


@route(__tag, no_end_slash=True, methods=["DELETE"])
def delete_tag(request: Request, id: str) -> Dict:
    try:
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/tag/delete_by_id.sql")
            cursor.execute(query, id)
            conn.commit()
        return JSend.success(f"Deleted tag '{id}'")
    except DatabaseError as e:
        return JSend.fail(e.args[0])


@route(__tag, no_end_slash=True, methods=["PATCH"])
def patch_file(request: Request, id: str) -> RestResponse:
    body = request['BODY']
    payload = json.loads(body)

    required_fields = []
    optional_fields = [__data_schema['name'], __data_schema['description']]

    errors = []

    if validate_fields(payload, required_fields, optional_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        parts: List[str] = [f"{key} = :{key}" for key in payload]
        query = f"UPDATE tag SET {', '.join(parts)} WHERE id = :id"

        payload['id'] = id
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            cursor.execute(query, payload)
            conn.commit()
        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e.args[0])


@route(__tag, no_end_slash=True, methods=["PUT"])
def put_file(request: Request, id: str) -> RestResponse:
    body = request['BODY']
    payload = json.loads(body)

    required_fields = [__data_schema['name'], __data_schema['description']]
    opt_fields = []
    errors = []

    if validate_fields(payload, required_fields, opt_fields, errors):
        return JSend.fail(errors), ResponseCode.BAD_REQUEST
    try:
        payload['id'] = id
        with connect(config.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = 1")
            cursor = conn.cursor()
            query = read_sql_file("static/sql/tag/update.sql")
            cursor.execute(query, payload)
            conn.commit()

        return b'', ResponseCode.NO_CONTENT, {}
    except DatabaseError as e:
        return JSend.fail(e.args[0])
