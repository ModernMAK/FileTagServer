from sqlite3 import Cursor
from typing import Tuple

from pydantic import BaseModel

from FileTagServer.DBI.common import AbstractDBI


class AddSubFolderQuery(BaseModel):
    parent_id: int
    child_id: int


class AddSubFileQuery(BaseModel):
    folder_id: int
    file_id: int


class FolderChildrenDBI(AbstractDBI):
    def __run_exists(self, cursor: Cursor, path: str, args: Tuple) -> bool:
        sql = self.read_sql_file(path)
        cursor.execute(sql, args)
        row = cursor.fetchone()
        return row[0] == 1

    def __folder_exists(self, cursor: Cursor, id: int) -> bool:
        path = "folder/exists.sql"
        args = (str(id),)
        return self.__run_exists(cursor, path, args)

    def __file_exists(self, cursor: Cursor, id: int) -> bool:
        path = "file/exists.sql"
        args = (str(id),)
        return self.__run_exists(cursor, path, args)

    def __subfolder_exists(self, cursor: Cursor, id: int, child_id: int) -> bool:
        path = "folder_folder/exists.sql"
        args = (str(id), str(child_id))
        return self.__run_exists(cursor, path, args)

    def __subfile_exists(self, cursor: Cursor, id: int, file_id: int) -> bool:
        path = "folder_file/exists.sql"
        args = (str(id), str(file_id))
        return self.__run_exists(cursor, path, args)

    def add_folder_to_folder(self, query: AddSubFolderQuery):
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder_folder/insert.sql")
            args = str(query.parent_id), str(query.child_id)
            cursor.execute(sql, args)
            conn.commit()

    def add_file_to_folder(self, query: AddSubFileQuery):
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("folder_file/insert.sql")
            args = str(query.folder_id), str(query.file_id)
            cursor.execute(sql, args)
            conn.commit()
