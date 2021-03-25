from http import HTTPStatus
from typing import List, Tuple, Dict, Optional
from sqlite3 import Row

from litespeed import serve
from litespeed.error import ResponseError

from src.api.common import __connect, create_sort_sql, validate_sort_fields
from src.rest.common import read_sql_file


def __query_helper(query_list: List[str], arg_list: List, query: str, args: List = None):
    if query is not None:
        query_list.append(query)
    if args is not None:
        arg_list.extend(args)


def __err_helper(key: str, errors: Dict, key_errors: Optional[List[str]]):
    if key_errors is not None:
        errors[key] = key_errors


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors


def get_files(sort: List[Tuple[str, bool]] = None) -> List[Row]:
    with __connect() as (conn, cursor):
        select_files = read_sql_file("static/sql/file/select.sql", True)
        args = []
        errors = {}
        queries: List[str] = []
        # SORT
        allowed_sorts = ['id', 'name', 'mime', 'description', 'path']
        __err_helper("sort", errors, validate_sort_fields(sort, allowed_sorts, allowed_sorts))
        __query_helper(queries, args, create_sort_sql(sort))

        if len(errors) > 0:
            raise ValidationError(errors)

        query = select_files if len(queries) == 0 else f"SELECT * FROM ({select_files}) {' '.join(queries)}"
        cursor.execute(query, args)
        return cursor.fetchall()


def get_files_tags(sort: List[Tuple[str, bool]] = None) -> List[Row]:
    with __connect() as (conn, cursor):
        select_files = read_sql_file("static/sql/file/select.sql", True)
        args = []
        errors = {}
        queries: List[str] = []
        # SORT
        allowed_sorts = ['id', 'name', 'mime', 'description', 'path']
        __err_helper("sort", errors, validate_sort_fields(sort, allowed_sorts, allowed_sorts))
        __query_helper(queries, args, create_sort_sql(sort))

        if len(errors) > 0:
            raise ValidationError(errors)

        file_query = select_files if len(queries) == 0 else f"SELECT * FROM ({select_files}) {' '.join(queries)}"
        file_query = f"SELECT id FROM ({file_query})"
        query = read_sql_file("static/sql/tag/select_by_file_query.sql").replace("<file_query>", file_query)
        cursor.execute(query, args)
        return cursor.fetchall()


def get_file(id: int) -> Row:
    with __connect() as (conn, cursor):
        query = read_sql_file("static/sql/file/select_by_id.sql")
        cursor.execute(query, str(id))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No file found with the given id: '{id}'")
        elif len(rows) > 1:
            raise ResponseError(HTTPStatus.MULTIPLE_CHOICES, f"Too many files found with the given id: '{id}'")
        return rows[0]


def get_file_tags(id: int) -> List[Row]:
    with __connect() as (conn, cursor):
        query = read_sql_file("static/sql/tag/select_by_file_id.sql")
        cursor.execute(query, str(id))
        return cursor.fetchall()


def get_file_data(id: int, range: str = None):
    result = get_file(id)
    local_path = result['path']
    return serve(local_path, range=range, headers={"Accept-Ranges": "bytes"})
