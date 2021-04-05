from http import HTTPStatus
from sqlite3 import Row, Cursor
from typing import List, Dict, Optional, Union, Any, Set
from litespeed import serve
from litespeed.error import ResponseError
from pydantic import BaseModel, validator, Field
from src.api.common import __connect, SortQuery, Util, validate_fields, row_to_tag, row_to_file
from src.api.models import File, Tag
from src.rest.common import read_sql_file


def __exists(cursor: Cursor, id: int) -> bool:
    sql = read_sql_file("static/sql/file/exists.sql")
    cursor.execute(sql, str(id))
    row = cursor.fetchone()
    return row[0] == 1


class FilesQuery(BaseModel):
    sort: Optional[List[SortQuery]] = None
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    # Validators
    @validator('sort', each_item=True)
    def validate_sort(cls, value: SortQuery) -> SortQuery:
        # will raise error if failed
        validate_fields(value.field, File.__fields__)
        return value

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


def get_files(query: FilesQuery) -> List[File]:
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
        tags = {tag.id: tag for tag in get_files_tags(query)}
        results = [row_to_file(row, tag_lookup=tags) for row in rows]
        if query.fields is not None:
            results = Util.copy(results, include=set(query.fields))
        return results


def get_files_tags(query: FilesQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        get_files_sql = read_sql_file("static/sql/file/select.sql", True)
        # SORT
        if query.sort is not None:
            sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
        else:
            sort_query = ''

        sql = f"SELECT id from ({get_files_sql} {sort_query})"
        sql = read_sql_file("static/sql/tag/select_by_file_query.sql").replace("<file_query>", sql)
        cursor.execute(sql)
        rows = cursor.fetchall()

        def row_to_tag(r: Row) -> Tag:
            r: Dict = dict(r)
            return Tag(**r)

        results = [row_to_tag(row) for row in rows]
        if query.tag_fields is not None:
            results = Util.copy(results, include=set(query.tag_fields))
        return results


class FileTagQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class FileQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self) -> FileTagQuery:
        return FileTagQuery(id=self.id, fields=self.tag_fields)


class CreateFileQuery(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = Field(default_factory=lambda: [])

    def create_file(self, id: int, tags: List[Tag]) -> File:
        return File(id=id, path=self.path, name=self.name, description=self.description, tags=tags)


def get_file(query: FileQuery) -> File:
    with __connect() as (conn, cursor):
        sql = read_sql_file("static/sql/file/select_by_id.sql")
        cursor.execute(sql, str(query.id))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No file found with the given id: '{query.id}'")
        elif len(rows) > 1:
            raise ResponseError(HTTPStatus.MULTIPLE_CHOICES, f"Too many files found with the given id: '{query.id}'")
        tags = get_file_tags(query.create_tag_query())
        result = row_to_file(rows[0], tags=tags)
        if query.fields is not None:
            result = result.copy(include=set(query.fields))
        return result


def create_file(query: CreateFileQuery) -> File:
    with __connect() as (conn, cursor):
        sql = read_sql_file("static/sql/file/insert.sql")
        cursor.execute(sql, query.json())
        conn.commit()
        id = cursor.lastrowid
        tags = get_file_tags(FileTagQuery(id=id)) if query.tags is not None else None
        return query.create_file(id=id, tags=tags)


def get_file_tags(query: FileTagQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        if not __exists(cursor, query.id):
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No file found with the given id: '{query.id}'")

        sql = read_sql_file("static/sql/tag/select_by_file_id.sql")
        cursor.execute(sql, str(query.id))
        results = [row_to_tag(row) for row in cursor.fetchall()]
        if query.fields is not None:
            results = Util.copy(results, include=set(query.fields))
        return results


class FileDataQuery(BaseModel):
    id: int
    range: Optional[str] = None


def get_file_bytes(query: FileDataQuery):
    result = get_file(FileQuery(id=query.id))
    local_path = result.path
    return serve(local_path, range=query.range, headers={"Accept-Ranges": "bytes"})
