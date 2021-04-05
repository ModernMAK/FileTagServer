import json
import urllib.parse
from os.path import join
from typing import List, Dict, Union, Tuple, Type, Any
from litespeed import App, start_with_args, route
from src.util.litespeedx import Response, Request, JSend
from sqlite3 import connect, Row, DatabaseError
from http import HTTPStatus as ResponseCode

RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]


def url_protocol(protocol: str, url: str) -> str:
    if protocol is None:
        return url
    stripped_url = url.lstrip("/\\")
    delimiter = "//"
    if protocol.lower() == "file":  # Special case uses 3 '/'
        delimiter = "///"
    return protocol + ":" + delimiter + stripped_url


def url_join(*paths: str) -> str:
    URL_SLASH = "/"
    SLASHES = ['\\', '/']
    path = ""
    prev_empty = True
    for part in paths:
        part = str(part)
        if part is None:
            if prev_empty:
                continue
            else:
                path += URL_SLASH
                prev_empty = True
                continue
        else:
            prev_empty = False
            if part[0] in SLASHES:
                path = part
            else:
                if len(path) > 0 and path[-1] not in SLASHES:
                    path += URL_SLASH
                path += part
    return path


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


def init_tables(db_path):
    with connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(read_sql_file("static/sql/file/create.sql"))
        cursor.execute(read_sql_file("static/sql/tag/create.sql"))
        cursor.execute(read_sql_file("static/sql/file_tag/create.sql"))
        conn.commit()


def parse_field_request(get_args: Dict[str, str], allowed_fields: List[str], errors: List[str], separator=',') -> Union[
    None, List[str]]:
    if "fields" not in get_args:
        return None
    fields = get_args["fields"].split(separator)
    results = []
    for field in fields:
        if field not in allowed_fields:
            errors.append(f"Cannot return field '{field}'; it is not allowed or does not exist.")
        else:
            results.append(field)
    return results


def parse_offset_request(get_args: Dict[str, str], errors: List[str], default_limit: int = 50) -> Union[
    None, Tuple[int, Union[int, None]]]:
    limit = get_args.get("limit")
    offset = get_args.get("offset")
    using_limit_offset = limit is not None or offset is not None

    page = get_args.get("page")
    size = get_args.get("size")
    using_page_size = page is not None or size is not None

    if using_limit_offset and using_page_size:
        errors.append("Cannot use both Page-Size and Limit-Offset Modes")
        return None
    if not using_limit_offset or not using_page_size:
        return default_limit, None

    if using_page_size:
        if page is not None:
            page = int(page)
            offset = (page - 1) * size
        if size is None:
            size = default_limit
        else:
            size = int(size)
        limit = size
    else:
        if offset is not None:
            offset = int(offset)

        if limit is None:
            limit = default_limit
        else:
            limit = int(size)
    return limit, offset

#
# def parse_sort_request(get_args: Dict[str, str], allowed_fields: List[str], errors: List[str]) -> Union[
#     None, List[Tuple[str, bool]]]:
#     order_by = get_args.get("sort")
#     if order_by is None:
#         return None
#     pairs = order_by.split(",")
#     formatted_pairs = []
#     for pair in pairs:
#         asc = True
#         name = pair.strip()
#         if pair[0] == "+":
#             asc = True
#             name = pair[1:].strip()
#         elif pair[0] == "-":
#             asc = False
#             name = pair[1:].strip()
#         if name not in allowed_fields:
#             errors.append(f"Unexpected field in order_by clause: '{name}'")
#         formatted_pairs.append((name, asc))
#     return formatted_pairs
