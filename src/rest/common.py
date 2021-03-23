import json
from os.path import join
from typing import List, Dict, Union, Tuple, Type, Any
from litespeed import App, start_with_args, route
from src.util.litespeedx import Response, Request, JSend
from sqlite3 import connect, Row, DatabaseError
from http import HTTPStatus as ResponseCode

db_path = "local.db"
RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]


def read_sql_file(file: str, strip_terminal=False):
    with open(file, "r") as f:
        r = f.read()
        if strip_terminal and r[-1] == ';':
            return r[:-1]
        else:
            return r


def reformat_url(url: str, base: str = None):
    if base is None:
        base = "http://localhost:8000"
    return join(base, url)


def validate_required_fields(d: Dict, fields: List[Dict], errors: List[str]):
    for field in fields:
        allowed_types = field['types']
        typename = field['type_description']
        name = field['name']
        if name not in d:
            errors.append(f"Missing required field: '{field}'")
        elif not isinstance(d[name], allowed_types):
            errors.append(f"Field '{name}' did not receive expected type '{typename}', received '{d[name]}'")


def validate_expected_fields(d: Dict, fields: List[Dict], errors: List[str]):
    for field in fields:
        allowed_types = field['types']
        typename = field['type_description']
        name = field['name']
        if name in d and not isinstance(d[name], allowed_types):
            errors.append(f"Field '{field}' did not receive expected type '{typename}', received '{d[field]}'")


def validate_unexpected_fields(d: Dict, fields: List[str], errors: List[str]):
    for field in d:
        if field not in fields:
            errors.append(f"Unknown field received: '{field}'")


def populate_optional(d: Dict, fields: List[Dict]):
    for field in fields:
        name = field['name']
        if name not in d:
            d[name] = None


def validate_fields(d: Dict, req_fields: List[Dict], opt_fields: List[Dict],
                    errors: List[str]):
    validate_required_fields(d, req_fields, errors)
    validate_expected_fields(d, opt_fields, errors)
    req_field_names = [f['name'] for f in req_fields]
    opt_field_names = [f['name'] for f in opt_fields]
    exp_field_names = req_field_names + opt_field_names
    validate_unexpected_fields(d, exp_field_names, errors)
    return len(errors) > 0


def init_tables():
    with connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(read_sql_file("static/sql/file/create.sql"))
        cursor.execute(read_sql_file("static/sql/tag/create.sql"))
        cursor.execute(read_sql_file("static/sql/file_tag/create.sql"))
        conn.commit()

if __name__ == "__main__":
    import src.rest.file
    import src.rest.tag
    init_tables()
    start_with_args()
