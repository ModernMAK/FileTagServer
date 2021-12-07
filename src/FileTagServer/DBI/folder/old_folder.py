from sqlite3 import Cursor
from typing import List, Optional, Union, Tuple
from pydantic import BaseModel, validator, Field
from starlette import status

from FileTagServer.DBI.common import _connect, SortQuery, Util, validate_fields, row_to_tag, row_to_folder, \
    read_sql_file
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.file.old_file import FileQuery, get_file
from FileTagServer.DBI.old_models import Folder, File, Tag


def __run_exists(cursor: Cursor, path: str, args: Tuple) -> bool:
    sql = read_sql_file(path)
    cursor.execute(sql, args)
    row = cursor.fetchone()
    return row[0] == 1


def __folder_exists(cursor: Cursor, id: int) -> bool:
    path = "../static/sql/folder/exists.sql"
    args = (str(id),)
    return __run_exists(cursor, path, args)


def __folder_tag_exists(cursor: Cursor, id: int, tag_id: int) -> bool:
    path = "../static/sql/fold_tag/exists.sql"
    args = (str(id), str(tag_id))
    return __run_exists(cursor, path, args)


class FoldersQuery(BaseModel):
    sort: Optional[List[SortQuery]] = None
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    # Validators
    @validator('sort', each_item=True)
    def validate_sort(cls, value: SortQuery) -> SortQuery:
        # will raise error if failed
        validate_fields(value.field, Folder.__fields__)
        return value

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class FolderTagQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class ModifyFolderQuery(BaseModel):
    path: Optional[str] = None
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None


class FullModifyFolderQuery(ModifyFolderQuery):
    id: int


class SetFolderQuery(BaseModel):
    # Optional[...] without '= None' means the field is required BUT can be none
    path: str
    mime: Optional[str]
    name: Optional[str]
    description: Optional[str]
    # Tags are special: a put query allows them to be optional, since they can be set at a seperate endpoint
    tags: Optional[List[int]] = None


class FullSetFolderQuery(SetFolderQuery):
    id: int


class FolderQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self) -> FolderTagQuery:
        return FolderTagQuery(id=self.id, fields=self.tag_fields)


class FolderPathQuery(BaseModel):
    path: str

    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self, id: int) -> FolderTagQuery:
        return FolderTagQuery(id=id, fields=self.tag_fields)


class CreateFolderQuery(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None

    def create_folder(self, id: int, tags: List[Tag]) -> Folder:
        return Folder(id=id, path=self.path, name=self.name, description=self.description, tags=tags)


class SearchQuery(BaseModel):
    # AND
    required: Optional[List[Union['SearchQuery', str]]] = None
    # OR
    include: Optional[List[Union['SearchQuery', str]]] = None
    # NOT
    exclude: Optional[List[Union['SearchQuery', str]]] = None


class FolderSearchQuery(BaseModel):
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None
    sort: Optional[List[SortQuery]] = None
    search: Optional[SearchQuery] = None
    page: Optional[int] = Field(1, ge=1)

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


#
# def get_folders(query: FoldersQuery) -> List[Folder]:
#     with __connect() as (conn, cursor):
#         get_folders_sql = read_sql_file("../static/sql/folder/select.sql", True)
#         # SORT
#         if query.sort is not None:
#             sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
#         else:
#             sort_query = ''
#
#         sql = f"{get_folders_sql} {sort_query}"
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#         tags = {tag.id: tag for tag in get_folders_tags(query)}
#         results = [row_to_folder(row, tag_lookup=tags) for row in rows]
#         if query.fields is not None:
#             results = Util.copy(results, include=set(query.fields))
#         return results
#
#
# def get_folders_tags(query: FoldersQuery) -> List[Tag]:
#     with __connect() as (conn, cursor):
#         get_folders_sql = read_sql_file("../static/sql/folder/select.sql", True)
#         # SORT
#         if query.sort is not None:
#             sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
#         else:
#             sort_query = ''
#
#         sql = f"SELECT id from ({get_folders_sql} {sort_query})"
#         sql = read_sql_file("../static/sql/tag/select_by_folder_query.sql").replace("<folder_query>", sql)
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#
#         def row_to_tag(r: Row) -> Tag:
#             r: Dict = dict(r)
#             return Tag(**r)
#
#         results = [row_to_tag(row) for row in rows]
#         if query.tag_fields is not None:
#             results = Util.copy(results, include=set(query.tag_fields))
#         return results


def __get_folder(path:str, id: int) -> Folder:
    with _connect(path) as (conn, cursor):
        sql = read_sql_file("../static/sql/folder/select_by_id.sql")
        cursor.execute(sql, (str(id),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{id}'")
        elif len(rows) > 1:
            raise ApiError(status.HTTP_300_MULTIPLE_CHOICES, f"Too many folders found with the given id: '{id}'")
        return row_to_folder(rows[0])


def __get_subfolders(path:str, id: int) -> List[Folder]:
    with _connect(path) as (conn, cursor):
        sql = read_sql_file("../static/sql/folder_folder/get_subfolders.sql")
        cursor.execute(sql, (str(id),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No subfolders found for the given folder id: '{id}'")

        result = [__get_folder(path,row['child_id']) for row in rows]
        return result


def __get_file(path:str, id: int) -> File:
    return get_file(path,FileQuery(id=id))


def __get_subfiles(path:str, id: int) -> List[File]:
    with _connect(path) as (conn, cursor):
        sql = read_sql_file("../static/sql/folder_file/get_subfiles.sql")
        cursor.execute(sql, (str(id),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No subfiles found for the given folder id: '{id}'")

        result = [__get_file(row['file_id']) for row in rows]
        return result


def get_folder(path:str, query: FolderQuery) -> Folder:
    folder = __get_folder(path,query.id)
    try:
        folder.subfolders = __get_subfolders(path,query.id)
    except ApiError:
        folder.subfolders = []

    try:
        folder.files = __get_subfiles(path,query.id)
    except ApiError:
        folder.files = []

    folder.tags = []
    return folder


def get_root_folders(path:str) -> List[Folder]:
    with _connect(path) as (conn, cursor):
        sql = read_sql_file("../static/sql/folder_folder/get_root_folders.sql")
        cursor.execute(sql)  # , (str(query.id),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No root folders?! Perhaps the database is empty?")
        folders = [get_folder(path,FolderQuery(id=r['parent_id'])) for r in rows]
        return folders


def get_folder_by_path(path:str,query: FolderPathQuery) -> Folder:
    with _connect(path) as (conn, cursor):
        sql = read_sql_file("../static/sql/folder/select_by_path.sql")
        cursor.execute(sql, (str(query.path),))
        rows = cursor.fetchall()
        if len(rows) < 1:
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given path: '{query.path}'")
        elif len(rows) > 1:
            raise ApiError(status.HTTP_300_MULTIPLE_CHOICES,
                           f"Too many folders found with the given path: '{query.path}'")
        result = row_to_folder(rows[0])
        # tags = get_folder_tags(query.create_tag_query(id=result.id))
        # result = row_to_folder(rows[0], tags=tags)
        if query.fields is not None:
            result = result.copy(include=set(query.fields))
        return result


def create_folder(path:str,query: CreateFolderQuery) -> Folder:
    with _connect(path) as (conn, cursor):
        sql = read_sql_file("../static/sql/folder/insert.sql")
        sql_args = query.dict(include={'path', 'description', 'name'})
        cursor.execute(sql, sql_args)
        id = cursor.lastrowid
        tags = []
        if query.tags is not None and len(query.tags) > 0:
            raise ApiError(status.HTTP_501_NOT_IMPLEMENTED)
            # TODO impliment tags
            # set_folder_tags(SetFolderTagsQuery)
            # tags = get_folder_tags(FolderTagQuery(id=id))

        conn.commit()
        return query.create_folder(id=id, tags=tags)


class DeleteFolderQuery(BaseModel):
    id: int


def delete_folder(path:str,query: DeleteFolderQuery):
    with _connect(path) as (conn, cursor):
        if not __folder_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
        sql = read_sql_file("../static/sql/folder/delete_by_id.sql")
        cursor.execute(sql, str(query.id))
        conn.commit()


# Does not commit
def set_folder_tags(cursor: Cursor, folder_id: int, tags: List[int]):
    q = FolderTagQuery(id=folder_id, fields=["id"])
    current_tags = get_folder_tags(q)
    current_ids = [tag.id for tag in current_tags]
    # ADD PASS
    add_sql = read_sql_file("../static/sql/folder_tag/insert.sql")
    for tag in tags:
        if tag not in current_ids:
            args = (str(folder_id), str(tag))
            cursor.execute(add_sql, args)
    # DEL PASS
    del_sql = read_sql_file("../static/sql/folder_tag/delete_pair.sql")
    for tag in current_ids:
        if tag not in tags:
            args = {'folder_id': folder_id, 'tag_id': tag}
            cursor.execute(del_sql, args)


def modify_folder(path:str,query: FullModifyFolderQuery):
    json = query.dict(exclude={'id', 'tags'}, exclude_unset=True)
    parts: List[str] = [f"{key} = :{key}" for key in json]
    sql = f"UPDATE folder SET {', '.join(parts)} WHERE id = :id"
    json['id'] = query.id

    with _connect(path) as (conn, cursor):
        if not __folder_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
        cursor.execute(sql, json)
        if query.tags is not None:
            set_folder_tags(cursor, query.id, query.tags)
        conn.commit()


def set_folder(path:str,query: FullSetFolderQuery) -> None:
    sql = read_sql_file("../static/sql/folder/update.sql")
    args = query.dict(exclude={'tags'})
    # HACK while tags is not implimented
    if query.tags is not None:
        raise NotImplementedError

    with _connect(path) as (conn, cursor):
        if not __folder_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
        cursor.execute(sql, args)
        conn.commit()
        # return True
    # return b'', ResponseCode.NO_CONTENT, {}


def get_folder_tags(path:str,query: FolderTagQuery) -> List[Tag]:
    with _connect(path) as (conn, cursor):
        if not __folder_exists(cursor, query.id):
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
        sql = read_sql_file("../static/sql/tag/select_by_folder_id.sql")
        cursor.execute(sql, (str(query.id),))
        results = [row_to_tag(row) for row in cursor.fetchall()]
        if query.fields is not None:
            results = Util.copy(results, include=set(query.fields))
        return results


def folder_has_tag(path:str,folder_id: int, tag_id: int) -> bool:
    with _connect(path) as (conn, cursor):
        if not __folder_exists(cursor, folder_id):
            raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{folder_id}'")
        return __folder_tag_exists(cursor, folder_id, tag_id)


class FolderDataQuery(BaseModel):
    id: int
    range: Optional[str] = None


def get_folder_path(folder_id: int) -> Optional[str]:
    # Dont need to check; it will raise an DBI error if it fails to get the folder
    # Parent functions should handle the error as they need
    folder = get_folder(FolderQuery(id=folder_id, fields=["path"]))
    return folder.path


def get_folder_bytes(query: FolderDataQuery):
    raise Exception("This function is depricated. Please use get_folder_path and open manually")
    # result = get_folder(FolderQuery(id=query.id))
    # local_path = result.path
    # return serve(local_path, range=query.range, headers={"Accept-Ranges": "bytes"})


def search_folders(query: FolderSearchQuery) -> List[Folder]:
    sort_sql = SortQuery.list_sql(query.sort) if query.sort else None

    if sort_sql:
        raise NotImplementedError
    return []
