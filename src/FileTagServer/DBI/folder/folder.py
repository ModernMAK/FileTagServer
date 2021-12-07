from sqlite3 import Row
from typing import List, Dict

from FileTagServer.DBI.common import replace_kwargs, AbstractDBI
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.folder import queries
from FileTagServer.DBI.models import Folder


class FolderDBI(AbstractDBI):
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
