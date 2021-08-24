from sqlite3 import Row, Cursor
from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel, validator, Field
from starlette import status

from FileTagServer.DBI.common import __connect, SortQuery, Util, validate_fields, row_to_tag, row_to_folder, \
    read_sql_file
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.models import Folder, File, Tag


def __run_exists(cursor: Cursor, path: str, args: Tuple) -> bool:
    sql = read_sql_file(path)
    cursor.execute(sql, args)
    row = cursor.fetchone()
    return row[0] == 1


def __folder_exists(cursor: Cursor, id: int) -> bool:
    path = "../static/sql/folder/exists.sql"
    args = (str(id),)
    return __run_exists(cursor, path, args)


def __file_exists(cursor: Cursor, id: int) -> bool:
    path = "../static/sql/file/exists.sql"
    args = (str(id),)
    return __run_exists(cursor, path, args)


def __subfolder_exists(cursor: Cursor, id: int, child_id: int) -> bool:
    path = "../static/sql/folder_folder/exists.sql"
    args = (str(id), str(child_id))
    return __run_exists(cursor, path, args)


def __subfile_exists(cursor: Cursor, id: int, file_id: int) -> bool:
    path = "../static/sql/folder_file/exists.sql"
    args = (str(id), str(file_id))
    return __run_exists(cursor, path, args)


class AddSubFolderQuery(BaseModel):
    parent_id: int
    child_id: int


class AddSubFileQuery(BaseModel):
    folder_id: int
    file_id: int


def add_folder_to_folder(query: AddSubFolderQuery):
    with __connect() as (conn, cursor):
        sql = read_sql_file("../static/sql/folder_folder/insert.sql")
        args = str(query.parent_id), str(query.child_id)
        cursor.execute(sql, args)
        conn.commit()


def add_file_to_folder(query: AddSubFileQuery):
    with __connect() as (conn, cursor):
        sql = read_sql_file("../static/sql/folder_file/insert.sql")
        args = str(query.folder_id), str(query.file_id)
        cursor.execute(sql, args)
        conn.commit()
