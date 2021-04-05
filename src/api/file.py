from http import HTTPStatus
from typing import List, Tuple, Dict, Optional, Union, Any, Set
from sqlite3 import Row
from litespeed import serve
from litespeed.error import ResponseError
from pydantic import BaseModel, validator, Field, ValidationError
from src.api.common import __connect, SortQuery, Util
from src.api.models import File, Tag
from src.rest.common import read_sql_file


# from src.rest.ttt import Util


def validate_fields(value: str, fields: Union[List[str], Dict[str, Any], Set[str]]) -> str:
    if value not in fields:
        quoted_fields = [f'\'{f}\'' for f in fields]
        raise ValueError(f"Field '{value}' not allowed! Allowed fields: {', '.join(quoted_fields)}")
    return value


def row_to_file(r: Row, *, tags: List[Tag] = None, tag_lookup: Dict[int, Tag] = None, ) -> File:
    r: Dict = dict(r)
    if tags:
        r['tags'] = tags
    elif r['tags'] is not None:
        if tag_lookup:
            f_tags = r['tags']
            f_tags = [int(id) for id in f_tags.split(",")]
            r['tags'] = [tag_lookup[id] for id in f_tags]
    else:
        r['tags'] = []
    return File(**r)


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


class CreateFileQuery(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = Field(default_factory=lambda: [])


def get_file(query: FileQuery) -> File:
    with __connect() as (conn, cursor):
        sql = read_sql_file("static/sql/file/select_by_id.sql")
        cursor.execute(sql, str(query.id))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No file found with the given id: '{query.id}'")
        elif len(rows) > 1:
            raise ResponseError(HTTPStatus.MULTIPLE_CHOICES, f"Too many files found with the given id: '{query.id}'")
        tags = get_file_tags(query)
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
        return File(id=id, **query.dict())


def get_file_tags(query: FileQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        sql = read_sql_file("static/sql/tag/select_by_file_id.sql")
        cursor.execute(sql, str(query.id))
        results = [Tag(**dict(row)) for row in cursor.fetchall()]
        if query.tag_fields is not None:
            results = Util.copy(results, include=set(query.tag_fields))
        return results


class FileDataQuery(BaseModel):
    id: int
    range: Optional[str] = None


def get_file_bytes(query: FileDataQuery):
    result = get_file(FileQuery(id=query.id))
    local_path = result.path
    return serve(local_path, range=query.range, headers={"Accept-Ranges": "bytes"})
#
#
# sqa = SortQuery(field='id')
# sqa2 = SortQuery(field='id', ascending=False)
# sqb = SortQuery(field='name', ascending=False)
# sqb2 = SortQuery(field='name', ascending=True)
#
# print(sqa)
# print(sqb)
#
# print("\nQ1A")
# fq = FilesQuery(sort=[sqa, sqb])
# print(fq)
# files = get_files(fq)
# print(files)
# print("\nQ1B")
# fq = FilesQuery(sort=[sqa2, sqb2])
# print(fq)
# files = get_files(fq)
# print(files)
# print("\nQ2")
# fq = FilesQuery(sort=[sqa, sqb], fields=["id", "name", "tags"], tag_fields=['id'])
# print(fq)
# files = get_files(fq)
# print(files)
# print("\nQ3")
# fq = FilesQuery(sort=[sqa, sqb], tag_fields=['id'])
# print(fq)
# files = get_files(fq)
# print(files)
# print("\nQ4")
# fq = FilesQuery(sort=[sqa, sqb], fields=["id", "name", "tags"])
# print(fq)
# files = get_files(fq)
# print(files)
