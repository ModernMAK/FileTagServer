from sqlite3 import Cursor
from sqlite3 import Row
from typing import Dict
from typing import List, Optional, Tuple

from starlette import status

from FileTagServer.DBI.common import SortQuery, Util, row_to_tag, row_to_folder
from FileTagServer.DBI.common import replace_kwargs, AbstractDBI
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.file.models import FileQuery
from FileTagServer.DBI.folder import queries
from FileTagServer.DBI.folder.models import FolderSearchQuery, FolderQuery, FolderTagQuery, FullSetFolderQuery, FullModifyFolderQuery, DeleteFolderQuery, CreateFolderQuery, FolderPathQuery
from FileTagServer.DBI.models import Folder, File, Tag


class AbstractFolderDBI(AbstractDBI):
    def __run_exists(self, cursor: Cursor, path: str, args: Tuple) -> bool:
        sql = self.read_sql_file(path)
        cursor.execute(sql, args)
        row = cursor.fetchone()
        return row[0] == 1

    def __folder_exists(self, cursor: Cursor, id: int) -> bool:
        path = "folder/exists.sql"
        args = (str(id),)
        return self.__run_exists(cursor, path, args)

    def __folder_tag_exists(self, cursor: Cursor, id: int, tag_id: int) -> bool:
        path = "fold_tag/exists.sql"
        args = (str(id), str(tag_id))
        return self.__run_exists(self, cursor, path, args)

    def __get_folder(self, id: int) -> Folder:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder/select_by_id.sql")
            cursor.execute(sql, (str(id),))
            rows = cursor.fetchall()
            if len(rows) < 1:
                raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{id}'")
            elif len(rows) > 1:
                raise ApiError(status.HTTP_300_MULTIPLE_CHOICES, f"Too many folders found with the given id: '{id}'")
            return row_to_folder(rows[0])

    def __get_subfolders(self, id: int) -> List[Folder]:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder_folder/get_subfolders.sql")
            cursor.execute(sql, (str(id),))
            rows = cursor.fetchall()
            if len(rows) < 1:
                raise ApiError(status.HTTP_410_GONE, f"No subfolders found for the given folder id: '{id}'")

            result = [self.__get_folder(row['child_id']) for row in rows]
            return result


class FolderQueryDBI(AbstractFolderDBI):
    def __init__(self, db_filepath: str, sql_root: str):
        super().__init__(db_filepath, sql_root)

    def __get_file(self, path: str, id: int) -> File:
        raise NotImplementedError
        # return self.get_file(path, FileQuery(id=id))

    def __get_subfiles(self, id: int) -> List[File]:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder_file/get_subfiles.sql")
            cursor.execute(sql, (str(id),))
            rows = cursor.fetchall()
            if len(rows) < 1:
                raise ApiError(status.HTTP_410_GONE, f"No subfiles found for the given folder id: '{id}'")

            result = [self.__get_file(row['file_id']) for row in rows]
            return result

    def get_folder(self, query: FolderQuery) -> Folder:
        folder = self.__get_folder(query.id)
        try:
            folder.subfolders = self.__get_subfolders(query.id)
        except ApiError:
            folder.subfolders = []

        try:
            folder.files = self.__get_subfiles(query.id)
        except ApiError:
            folder.files = []

        folder.tags = []
        return folder

    def get_root_folders(self, path: str) -> List[Folder]:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder_folder/get_root_folders.sql")
            cursor.execute(sql)  # , (str(query.id),))
            rows = cursor.fetchall()
            if len(rows) < 1:
                raise ApiError(status.HTTP_410_GONE, f"No root folders?! Perhaps the database is empty?")
            folders = [self.get_folder(path, FolderQuery(id=r['id'])) for r in rows]
            return folders

    def get_folder_by_path(self, query: FolderPathQuery) -> Folder:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder/select_by_path.sql")
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

    def create_folder(self, query: CreateFolderQuery) -> Folder:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder/insert.sql")
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

    def delete_folder(self, query: DeleteFolderQuery):
        with self.connect() as (conn, cursor):
            if not self.__folder_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
            sql = self.read_sql_file("folder/delete_by_id.sql")
            cursor.execute(sql, str(query.id))
            conn.commit()

    # Does not commit
    def set_folder_tags(self, cursor: Cursor, folder_id: int, tags: List[int]):
        q = FolderTagQuery(id=folder_id, fields=["id"])
        current_tags = self.get_folder_tags(q)
        current_ids = [tag.id for tag in current_tags]
        # ADD PASS
        add_sql = self.read_sql_file("folder_tag/insert.sql")
        for tag in tags:
            if tag not in current_ids:
                args = (str(folder_id), str(tag))
                cursor.execute(add_sql, args)
        # DEL PASS
        del_sql = self.read_sql_file("folder_tag/delete_pair.sql")
        for tag in current_ids:
            if tag not in tags:
                args = {'folder_id': folder_id, 'tag_id': tag}
                cursor.execute(del_sql, args)

    def modify_folder(self, query: FullModifyFolderQuery):
        json = query.dict(exclude={'id', 'tags'}, exclude_unset=True)
        parts: List[str] = [f"{key} = :{key}" for key in json]
        # noinspection SqlResolve
        sql = f"UPDATE folder SET {', '.join(parts)} WHERE id = :id"
        json['id'] = query.id

        with self.connect() as (conn, cursor):
            if not self.__folder_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
            cursor.execute(sql, json)
            if query.tags is not None:
                self.set_folder_tags(cursor, query.id, query.tags)
            conn.commit()

    def set_folder(self, query: FullSetFolderQuery) -> None:
        sql = self.read_sql_file("folder/update.sql")
        args = query.dict(exclude={'tags'})
        # HACK while tags is not implimented
        if query.tags is not None:
            raise NotImplementedError

        with self.connect() as (conn, cursor):
            if not self.__folder_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
            cursor.execute(sql, args)
            conn.commit()
            # return True
        # return b'', ResponseCode.NO_CONTENT, {}

    def get_folder_tags(self, query: FolderTagQuery) -> List[Tag]:
        with self.connect() as (conn, cursor):
            if not self.__folder_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{query.id}'")
            sql = self.read_sql_file("tag/select_by_folder_id.sql")
            cursor.execute(sql, (str(query.id),))
            results = [row_to_tag(row) for row in cursor.fetchall()]
            if query.fields is not None:
                results = Util.copy(results, include=set(query.fields))
            return results

    def search_folders(self, query: FolderSearchQuery) -> List[Folder]:
        sort_sql = SortQuery.list_sql(query.sort) if query.sort else None
        if sort_sql:
            raise NotImplementedError
        return []


class FolderDBI(AbstractFolderDBI):
    def __init__(self, db_filepath: str, sql_root: str):
        super().__init__(db_filepath, sql_root)
        self.query = FolderQueryDBI(db_filepath, sql_root)

    @staticmethod
    def parse_row(row: Row) -> Folder:
        d: Dict = dict(row)
        if d['tags']:
            d['tags'] = [int(tag_id) for tag_id in d['tags'].split(",")]
        if d['subfolders']:
            d['subfolders'] = [int(tag_id) for tag_id in d['subfolders'].split(",")]
        if d['files']:
            d['files'] = [int(tag_id) for tag_id in d['files'].split(",")]
        return Folder(folders=d['subfolders'], **d)

    def get_folders(self, folder_ids: List[int]) -> List[Folder]:
        if not folder_ids:
            return []
        with self.connect() as (conn, cursor):
            sql_placeholder = ", ".join(["?" for _ in range(len(folder_ids))])
            sql = replace_kwargs(queries.select_by_ids, tag_ids=sql_placeholder)
            cursor.execute(sql, folder_ids)
            rows = cursor.fetchall()
            return [self.parse_row(row) for row in rows]

    def get_folder(self, folder_id: int) -> Folder:
        with self.connect() as (conn, cursor):
            cursor.execute(queries.select_by_id, (str(folder_id),))
            rows = cursor.fetchall()
            if len(rows) == 1:
                return self.parse_row(rows[0])
            elif len(rows) == 0:
                raise ApiError(404, f"Folder '{folder_id}' not found!")
            else:
                raise ApiError(300, f"Found '{len(rows)}' results for Folder '{folder_id}'!")

    def get_folder_by_path(self, path: str) -> Folder:
        if not path:
            raise ApiError(500, "Not Implemented")

        with self.connect() as (conn, cursor):
            cursor.execute(queries.select_by_path, (path,))
            rows = cursor.fetchall()
            if len(rows) == 1:
                return self.parse_row(rows[0])
            else:
                raise ApiError(500, "Not Implemented")

    def get_root_folders(self) -> List[Folder]:
        with self.connect() as (conn, cursor):
            cursor.execute(queries.select_root_folders)
            rows = cursor.fetchall()
            return [self.parse_row(row) for row in rows]

    # may not work

    def folder_has_tag(self, path: str, folder_id: int, tag_id: int) -> bool:
        with self.connect() as (conn, cursor):
            if not self.__folder_exists(cursor, folder_id):
                raise ApiError(status.HTTP_410_GONE, f"No folder found with the given id: '{folder_id}'")
            return self.__folder_tag_exists(cursor, folder_id, tag_id)

    def get_folder_path(self, folder_id: int) -> Optional[str]:
        # Dont need to check; it will raise an DBI error if it fails to get the folder
        # Parent functions should handle the error as they need
        folder = self.query.get_folder(FolderQuery(id=folder_id, fields=["path"]))
        return folder.path
