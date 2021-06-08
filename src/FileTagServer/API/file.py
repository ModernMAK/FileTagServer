from http import HTTPStatus
from sqlite3 import Row, Cursor
from typing import List, Dict, Optional, Union
from litespeed import serve
from litespeed.error import ResponseError
from pydantic import BaseModel, validator, Field
from src.FileTagServer.API.common import __connect, SortQuery, Util, validate_fields, row_to_tag, row_to_file
from src.FileTagServer.API.models import File, Tag
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


class FileTagQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class ModifyFileQuery(BaseModel):
    id: int
    path: Optional[str] = None
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None


class SetFileQuery(BaseModel):
    id: int
    # Optional[...] without '= None' means the field is required BUT can be none
    path: str
    mime: Optional[str]
    name: Optional[str]
    description: Optional[str]
    # Tags are special: a put query allows them to be optional, since they can be set at a seperate endpoint
    tags: Optional[List[int]] = None


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
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None

    def create_file(self, id: int, tags: List[Tag]) -> File:
        return File(id=id, path=self.path, name=self.name, description=self.description, tags=tags)


class SearchQuery(BaseModel):
    # AND
    required: Optional[List[Union['SearchQuery', str]]] = None
    # OR
    include: Optional[List[Union['SearchQuery', str]]] = None
    # NOT
    exclude: Optional[List[Union['SearchQuery', str]]] = None


class FileSearchQuery(BaseModel):
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None
    sort: Optional[List[SortQuery]] = None
    search: Optional[SearchQuery] = None
    page: Optional[int] = Field(1, ge=1)

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
        sql_args = query.dict(include={'path', 'mime', 'description', 'name'})
        cursor.execute(sql, sql_args)
        id = cursor.lastrowid
        tags = []
        if query.tags is not None:
            raise ResponseError(500)
            # TODO impliment tags
            # set_file_tags(SetFileTagsQuery)
            # tags = get_file_tags(FileTagQuery(id=id))

        conn.commit()
        return query.create_file(id=id, tags=tags)


class DeleteFileQuery(BaseModel):
    id: int


def delete_file(query: DeleteFileQuery) -> bool:
    with __connect() as (conn, cursor):
        if not __exists(cursor, query.id):
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No file found with the given id: '{query.id}'")
        sql = read_sql_file("static/sql/file/delete_by_id.sql")
        cursor.execute(sql, str(query.id))
        conn.commit()
    return True


def modify_file(query: ModifyFileQuery) -> bool:
    json = query.dict(exclude={'id', 'tags'}, exclude_unset=True)
    parts: List[str] = [f"{key} = :{key}" for key in json]
    sql = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"
    json['id'] = query.id

    # HACK while tags is not implimented
    if query.tags is not None:
        raise NotImplementedError

    with __connect() as (conn, cursor):
        if not __exists(cursor, query.id):
            raise ResponseError(HTTPStatus.NOT_FOUND)
        cursor.execute(query, sql)
        conn.commit()
        return True


def set_file(query: SetFileQuery) -> bool:
    sql = read_sql_file("static/sql/file/update.sql")
    args = query.dict(exclude={'tags'})
    # HACK while tags is not implimented
    if query.tags is not None:
        raise NotImplementedError

    with __connect() as (conn, cursor):
        if not __exists(cursor, query.id):
            raise ResponseError(HTTPStatus.NOT_FOUND)
        cursor.execute(sql, args)
        conn.commit()
        return True
    # return b'', ResponseCode.NO_CONTENT, {}


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


def search_files(query: FileSearchQuery) -> List[File]:
    sort_sql = SortQuery.list_sql(query.sort) if query.sort else None

    if sort_sql:
        raise NotImplementedError
    return []
