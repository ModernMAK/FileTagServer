from sqlite3 import Row, Cursor
from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel, validator, Field
from starlette import status

from FileTagServer.DBI.common import __connect, SortQuery, Util, validate_fields, row_to_tag, row_to_file, read_sql_file
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.models import File, Tag


def __run_exists(cursor: Cursor, path: str, args: Tuple) -> bool:
    sql = read_sql_file(path)
    cursor.execute(sql, args)
    row = cursor.fetchone()
    return row[0] == 1


def __file_exists(cursor: Cursor, id: int) -> bool:
    path = "../static/sql/file/exists.sql"
    args = (str(id),)
    return __run_exists(cursor, path, args)


def __file_tag_exists(cursor: Cursor, id: int, tag_id: int) -> bool:
    path = "../static/sql/file_tag/exists.sql"
    args = (str(id), str(tag_id))
    return __run_exists(cursor, path, args)


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
    path: Optional[str] = None
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None


class FullModifyFileQuery(ModifyFileQuery):
    id: int


class SetFileQuery(BaseModel):
    # Optional[...] without '= None' means the field is required BUT can be none
    path: str
    mime: Optional[str]
    name: Optional[str]
    description: Optional[str]
    # Tags are special: a put query allows them to be optional, since they can be set at a seperate endpoint
    tags: Optional[List[int]] = None


class FullSetFileQuery(SetFileQuery):
    id: int


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
        return File(id=id, path=self.path, mime=self.mime, name=self.name, description=self.description, tags=tags)


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


class FilePathQuery(BaseModel):
    path: str

    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self, id: int) -> FileTagQuery:
        return FileTagQuery(id=id, fields=self.tag_fields)


def get_files(query: FilesQuery) -> List[File]:
    with __connect() as (conn, cursor):
        get_files_sql = read_sql_file("../static/sql/file/select.sql", True)
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
        get_files_sql = read_sql_file("../static/sql/file/select.sql", True)
        # SORT
        if query.sort is not None:
            sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
        else:
            sort_query = ''

        sql = f"SELECT id from ({get_files_sql} {sort_query})"
        sql = read_sql_file("../static/sql/tag/select_by_file_query.sql").replace("<file_query>", sql)
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
        sql = read_sql_file("../static/sql/file/select_by_id.sql")
        cursor.execute(sql, (str(query.id),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
        elif len(rows) > 1:
            raise ApiError(status.HTTP_300_MULTIPLE_CHOICES, f"Too many files found with the given id: '{query.id}'")
        tags = get_file_tags(query.create_tag_query())
        result = row_to_file(rows[0], tags=tags)
        if query.fields is not None:
            result = result.copy(include=set(query.fields))
        return result


def get_file_by_path(query: FilePathQuery) -> File:
    with __connect() as (conn, cursor):
        sql = read_sql_file("../static/sql/file/select_by_path.sql")
        cursor.execute(sql, (str(query.path),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given path: '{query.path}'")
        elif len(rows) > 1:
            raise ApiError(status.HTTP_300_MULTIPLE_CHOICES,
                           f"Too many files found with the given path: '{query.path}'")
        result = row_to_file(rows[0])
        tags = get_file_tags(query.create_tag_query(id=result.id))
        result = row_to_file(rows[0], tags=tags)
        if query.fields is not None:
            result = result.copy(include=set(query.fields))
        return result


def create_file(query: CreateFileQuery) -> File:
    with __connect() as (conn, cursor):
        sql = read_sql_file("../static/sql/file/insert.sql")
        sql_args = query.dict(include={'path', 'mime', 'description', 'name'})
        cursor.execute(sql, sql_args)
        id = cursor.lastrowid
        tags = []
        if query.tags is not None and len(query.tags) > 0:
            raise ApiError(status.HTTP_501_NOT_IMPLEMENTED)
            # TODO impliment tags
            # set_file_tags(SetFileTagsQuery)
            # tags = get_file_tags(FileTagQuery(id=id))

        conn.commit()
        return query.create_file(id=id, tags=tags)


class DeleteFileQuery(BaseModel):
    id: int


def delete_file(query: DeleteFileQuery):
    with __connect() as (conn, cursor):
        if not __file_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
        sql = read_sql_file("../static/sql/file/delete_by_id.sql")
        cursor.execute(sql, str(query.id))
        conn.commit()


# Does not commit
def set_file_tags(cursor: Cursor, file_id: int, tags: List[int]):
    q = FileTagQuery(id=file_id, fields=["id"])
    current_tags = get_file_tags(q)
    current_ids = [tag.id for tag in current_tags]
    # ADD PASS
    add_sql = read_sql_file("../static/sql/file_tag/insert.sql")
    for tag in tags:
        if tag not in current_ids:
            args = (str(file_id), str(tag))
            cursor.execute(add_sql, args)
    # DEL PASS
    del_sql = read_sql_file("../static/sql/file_tag/delete_pair.sql")
    for tag in current_ids:
        if tag not in tags:
            args = {'file_id': file_id, 'tag_id': tag}
            cursor.execute(del_sql, args)


def modify_file(query: FullModifyFileQuery):
    json = query.dict(exclude={'id', 'tags'}, exclude_unset=True)
    parts: List[str] = [f"{key} = :{key}" for key in json]
    sql = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"
    json['id'] = query.id

    with __connect() as (conn, cursor):
        if not __file_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
        cursor.execute(sql, json)
        if query.tags is not None:
            set_file_tags(cursor, query.id, query.tags)
        conn.commit()


def set_file(query: FullSetFileQuery) -> None:
    sql = read_sql_file("../static/sql/file/update.sql")
    args = query.dict(exclude={'tags'})
    # HACK while tags is not implimented
    if query.tags is not None:
        raise NotImplementedError

    with __connect() as (conn, cursor):
        if not __file_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
        cursor.execute(sql, args)
        conn.commit()
        # return True
    # return b'', ResponseCode.NO_CONTENT, {}


def get_file_tags(query: FileTagQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        if not __file_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
        sql = read_sql_file("../static/sql/tag/select_by_file_id.sql")
        cursor.execute(sql, (str(query.id),))
        results = [row_to_tag(row) for row in cursor.fetchall()]
        if query.fields is not None:
            results = Util.copy(results, include=set(query.fields))
        return results


def file_has_tag(file_id: int, tag_id: int) -> bool:
    with __connect() as (conn, cursor):
        if not __file_exists(cursor, file_id):
            raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{file_id}'")
        return __file_tag_exists(cursor, file_id, tag_id)


class FileDataQuery(BaseModel):
    id: int
    range: Optional[str] = None


def get_file_path(file_id: int) -> Optional[str]:
    # Dont need to check; it will raise an DBI error if it fails to get the file
    # Parent functions should handle the error as they need
    file = get_file(FileQuery(id=file_id, fields=["path"]))
    return file.path


def get_file_bytes(query: FileDataQuery):
    raise Exception("This function is depricated. Please use get_file_path and open manually")
    # result = get_file(FileQuery(id=query.id))
    # local_path = result.path
    # return serve(local_path, range=query.range, headers={"Accept-Ranges": "bytes"})


def search_files(query: FileSearchQuery) -> List[File]:
    sort_sql = SortQuery.list_sql(query.sort) if query.sort else None

    if sort_sql:
        raise NotImplementedError
    return []
