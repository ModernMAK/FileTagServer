from http import HTTPStatus
from sqlite3 import Cursor
from typing import Optional, List

from litespeed.error import ResponseError
from pydantic import BaseModel, validator

from src.api.common import SortQuery, validate_fields, __connect, row_to_tag, Util
from src.api.models import Tag
from src.rest.common import read_sql_file


def __exists(cursor: Cursor, id: int) -> bool:
    sql = read_sql_file("static/sql/tag/exists.sql")
    cursor.execute(sql, str(id))
    row = cursor.fetchone()
    return row[0] == 1

class TagsQuery(BaseModel):
    sort: Optional[List[SortQuery]] = None
    fields: Optional[List[str]] = None

    # Validators
    @validator('sort', each_item=True)
    def validate_sort(cls, value: SortQuery) -> SortQuery:
        # will raise error if failed
        validate_fields(value.field, Tag.__fields__)
        return value

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class TagQuery(TagsQuery):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


def get_tags(query: TagsQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        get_files_sql = read_sql_file("static/sql/file/select.sql", True)
        # SORT
        if query.sort is not None:
            sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
        else:
            sort_query = ''

        sql = f"{get_files_sql} {sort_query}"
        cursor.execute(sql)
        rows = cursor.fetchall()
        results = [row_to_tag(row) for row in rows]
        if query.fields is not None:
            results = Util.copy(results, include=set(query.fields))
        return results


def get_tag(query: TagQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        sql = read_sql_file("static/sql/tag/select_by_id.sql")
        cursor.execute(sql, str(query.id))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No tag found with the given id: '{query.id}'")
        elif len(rows) > 1:
            raise ResponseError(HTTPStatus.MULTIPLE_CHOICES, f"Too many tags found with the given id: '{query.id}'")
        result = row_to_tag(rows[0])
        if query.fields is not None:
            result = Util.copy(result, include=set(query.fields))
        return result
