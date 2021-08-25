from sqlite3 import Row
from typing import List, Dict

from FileTagServer.DBI.common import __connect, replace_kwargs
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.file import queries
from FileTagServer.DBI.models import File


def parse_row(row: Row) -> File:
    d: Dict = dict(row)
    if d['tags']:
        d['tags'] = [int(tag_id) for tag_id in d['tags'].split(",")]
    return File(**d)


def get_files(file_ids: List[int]) -> List[File]:
    if not file_ids:
        return []
    with __connect() as (conn, cursor):
        sql_placeholder = ", ".join(["?" for _ in range(len(file_ids))])
        sql = replace_kwargs(queries.select_by_ids, file_ids=sql_placeholder)
        cursor.execute(sql, file_ids)
        rows = cursor.fetchall()
        return [parse_row(row) for row in rows]


def get_file(file_id: int) -> File:
    with __connect() as (conn, cursor):
        cursor.execute(queries.select_by_id, file_id)
        rows = cursor.fetchall()
        if len(rows) == 1:
            return parse_row(rows[0])
        else:
            raise ApiError(500, "Not Implemented")


def get_orphaned_files() -> List[File]:
    with __connect() as (conn, cursor):
        cursor.execute(queries.select_orphaned_files)
        rows = cursor.fetchall()
        return [parse_row(row) for row in rows]
