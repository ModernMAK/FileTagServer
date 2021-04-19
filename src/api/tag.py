from http import HTTPStatus
from sqlite3 import Cursor, DatabaseError, IntegrityError
from typing import Optional, List

from litespeed.error import ResponseError
from pydantic import BaseModel, validator

from src.api.common import SortQuery, validate_fields, __connect, row_to_tag, Util, AutoComplete
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


class TagQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class CreateTagQuery(TagsQuery):
    name: Optional[str] = None
    description: Optional[str] = None


class DeleteTagQuery(TagsQuery):
    id: int


class SetTagQuery(BaseModel):
    id: int
    # Optional[...] without '= None' means the field is required BUT can be none
    name: Optional[str]
    description: Optional[str]
    # Tags are special: a put query allows them to be optional, since they can be set at a seperate endpoint


class ModifyTagQuery(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None


def get_tags(query: TagsQuery) -> List[Tag]:
    with __connect() as (conn, cursor):
        get_files_sql = read_sql_file("static/sql/tag/select.sql", True)
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


def create_tag(query: CreateTagQuery) -> Tag:
    try:
        with __connect() as (conn, cursor):
            sql = read_sql_file("static/sql/tag/insert.sql")
            cursor.execute(sql, query.dict(include={'name', 'description'}))
            id = cursor.lastrowid
            conn.commit()
            return Tag(id=id, name=query.name, description=query.description)
    except IntegrityError as e:
        raise ResponseError(409, str(e))


def delete_tag(query: DeleteTagQuery) -> bool:
    with __connect() as (conn, cursor):
        if not __exists(cursor, query.id):
            raise ResponseError(HTTPStatus.NOT_FOUND, f"No tag found with the given id: '{query.id}'")
        sql = read_sql_file("static/sql/tag/delete_by_id.sql")
        cursor.execute(sql, str(query.id))
        conn.commit()
    return True


def set_tag(query: SetTagQuery) -> bool:
    try:
        sql = read_sql_file("static/sql/tag/update.sql")
        with __connect() as (conn, cursor):
            if not __exists(cursor, query.id):
                raise ResponseError(HTTPStatus.NOT_FOUND)
            cursor.execute(sql, query.dict())
            conn.commit()
            return True
    except IntegrityError as e:
        raise ResponseError(409, str(e))


def modify_tag(query: ModifyTagQuery) -> bool:
    json = query.dict(exclude={'id'}, exclude_unset=True)
    parts: List[str] = [f"{key} = :{key}" for key in json]
    sql = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"
    json['id'] = query.id

    with __connect() as (conn, cursor):
        if not __exists(cursor, query.id):
            raise ResponseError(HTTPStatus.NOT_FOUND)
        cursor.execute(query, sql)
        conn.commit()
        return True


def autocomplete_tag(name: str) -> List[AutoComplete]:
    escape_char = "/"
    try:
        with __connect() as (conn, cursor):
            sql = read_sql_file("static/sql/tag/autocomplete.sql")
            escaped = name.replace(escape_char, escape_char * 2).replace("%", f"{escape_char}%").replace("_", f"{escape_char}_")
            cursor.execute(sql, [f"%{escaped}%", escape_char])
            return [AutoComplete(value=row['name'].replace(" ", "_"), label=row['name']) for row in cursor.fetchall()]
    except DatabaseError as e:
        print(e)
        raise  # TODO figure out how to handle an err for autocomplete