from typing import List, Tuple, Dict, Optional
from sqlite3 import Row

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
