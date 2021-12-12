from sqlite3 import Row, Cursor
from typing import List, Dict, Optional, Tuple

from starlette import status

from FileTagServer.DBI.common import SortQuery, Util, row_to_tag, row_to_file
from FileTagServer.DBI.common import replace_kwargs, AbstractDBI
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.file import queries
from FileTagServer.DBI.file.models import FilesQuery, FileQuery, FilePathQuery, CreateFileQuery, DeleteFileQuery, FileTagQuery, FullModifyFileQuery, FullSetFileQuery, FileSearchQuery, FileDataQuery
from FileTagServer.DBI.models import File, Tag


class AbstractFileDBI(AbstractDBI):
    def _run_exists(self, cursor: Cursor, path: str, args: Tuple) -> bool:
        sql = self.read_sql_file(path)
        cursor.execute(sql, args)
        row = cursor.fetchone()
        return row[0] == 1

    def _file_exists(self, cursor: Cursor, id: int) -> bool:
        path = "file/exists.sql"
        args = (str(id),)
        return self._run_exists(cursor, path, args)

    def _file_tag_exists(self, cursor: Cursor, id: int, tag_id: int) -> bool:
        path = "file_tag/exists.sql"
        args = (str(id), str(tag_id))
        return self._run_exists(cursor, path, args)


class FileQueryDBI(AbstractFileDBI):
    def get_files(self, query: FilesQuery) -> List[File]:
        with self.connect() as (conn, cursor):
            get_files_sql = self.read_sql_file("file/select.sql")
            # SORT
            if query.sort is not None:
                sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
            else:
                sort_query = ''

            sql = f"{get_files_sql} {sort_query}"
            cursor.execute(sql)
            rows = cursor.fetchall()
            tags = {tag.id: tag for tag in self.get_files_tags(query)}
            results = [row_to_file(row, tag_lookup=tags) for row in rows]
            if query.fields is not None:
                results = Util.copy(results, include=set(query.fields))
            return results

    def get_files_tags(self, query: FilesQuery) -> List[Tag]:
        with self.connect() as (conn, cursor):
            get_files_sql = self.read_sql_file("file/select.sql")
            # SORT
            if query.sort is not None:
                sort_query = "ORDER BY " + SortQuery.list_sql(query.sort)
            else:
                sort_query = ''

            sql = f"SELECT id from ({get_files_sql} {sort_query})"
            sql = self.read_sql_file("tag/select_by_file_query.sql").replace("<file_query>", sql)
            cursor.execute(sql)
            rows = cursor.fetchall()

            def row_to_tag(r: Row) -> Tag:
                r: Dict = dict(r)
                return Tag(**r)

            results = [row_to_tag(row) for row in rows]
            if query.tag_fields is not None:
                results = Util.copy(results, include=set(query.tag_fields))
            return results

    def get_file(self, query: FileQuery) -> File:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("file/select_by_id.sql")
            cursor.execute(sql, (str(query.id),))
            rows = cursor.fetchall()
            if len(rows) < 1:
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
            elif len(rows) > 1:
                raise ApiError(status.HTTP_300_MULTIPLE_CHOICES, f"Too many files found with the given id: '{query.id}'")
            tags = self.get_file_tags(query.create_tag_query())
            result = row_to_file(rows[0], tags=tags)
            if query.fields is not None:
                result = result.copy(include=set(query.fields))
            return result

    def get_file_by_path(self, query: FilePathQuery) -> File:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("file/select_by_path.sql")
            cursor.execute(sql, (str(query.path),))
            rows = cursor.fetchall()
            if len(rows) < 1:
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given path: '{query.path}'")
            elif len(rows) > 1:
                raise ApiError(status.HTTP_300_MULTIPLE_CHOICES,
                               f"Too many files found with the given path: '{query.path}'")
            result = row_to_file(rows[0])
            tags = self.get_file_tags(query.create_tag_query(id=result.id))
            result = row_to_file(rows[0], tags=tags)
            if query.fields is not None:
                result = result.copy(include=set(query.fields))
            return result

    def create_file(self, query: CreateFileQuery) -> File:
        with self.connect() as (conn, cursor):
            sql = self.read_sql_file("file/insert.sql")
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

    def delete_file(self, query: DeleteFileQuery):
        with self.connect() as (conn, cursor):
            if not self._file_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
            sql = self.read_sql_file("file/delete_by_id.sql")
            cursor.execute(sql, str(query.id))
            conn.commit()

    def modify_file(self, query: FullModifyFileQuery):
        json = query.dict(exclude={'id', 'tags'}, exclude_unset=True)
        parts: List[str] = [f"{key} = :{key}" for key in json]
        sql = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"
        json['id'] = query.id

        with self.connect() as (conn, cursor):
            if not self._file_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
            cursor.execute(sql, json)
            if query.tags is not None:
                self._set_file_tags(cursor, query.id, query.tags)
            conn.commit()

    # Does not commit
    def _set_file_tags(self, cursor: Cursor, file_id: int, tags: List[int]):
        q = FileTagQuery(id=file_id, fields=["id"])
        current_tags = self.get_file_tags(q)
        current_ids = [tag.id for tag in current_tags]
        # ADD PASS
        add_sql = self.read_sql_file("file_tag/insert.sql")
        for tag in tags:
            if tag not in current_ids:
                args = (str(file_id), str(tag))
                cursor.execute(add_sql, args)
        # DEL PASS
        del_sql = self.read_sql_file("file_tag/delete_pair.sql")
        for tag in current_ids:
            if tag not in tags:
                args = {'file_id': file_id, 'tag_id': tag}
                cursor.execute(del_sql, args)


    def set_file(self, query: FullSetFileQuery) -> None:
        sql = self.read_sql_file("file/update.sql")
        args = query.dict(exclude={'tags'})
        # HACK while tags is not implimented
        if query.tags is not None:
            raise NotImplementedError

        with self.connect() as (conn, cursor):
            if not self._file_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
            cursor.execute(sql, args)
            conn.commit()
            # return True
        # return b'', ResponseCode.NO_CONTENT, {}

    def get_file_tags(self, query: FileTagQuery) -> List[Tag]:
        with self.connect() as (conn, cursor):
            if not self._file_exists(cursor, query.id):
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{query.id}'")
            sql = self.read_sql_file("tag/select_by_file_id.sql")
            cursor.execute(sql, (str(query.id),))
            results = [row_to_tag(row) for row in cursor.fetchall()]
            if query.fields is not None:
                results = Util.copy(results, include=set(query.fields))
            return results

    def get_file_bytes(self, query: FileDataQuery):
        raise Exception("This function is depricated. Please use get_file_path and open manually")
        # result = get_file(FileQuery(id=query.id))
        # local_path = result.path
        # return serve(local_path, range=query.range, headers={"Accept-Ranges": "bytes"})

    def search_files(self, query: FileSearchQuery) -> List[File]:
        sort_sql = SortQuery.list_sql(query.sort) if query.sort else None
        if sort_sql:
            raise NotImplementedError
        return []


class FileDBI(AbstractFileDBI):
    def __init__(self, db_filepath: str, sql_root: str):
        super().__init__(db_filepath, sql_root)
        self.query = FileQueryDBI(db_filepath, sql_root)

    @staticmethod
    def parse_row(row: Row) -> File:
        d: Dict = dict(row)
        if d['tags']:
            d['tags'] = [int(tag_id) for tag_id in d['tags'].split(",")]
        return File(**d)

    def get_files(self, file_ids: List[int]) -> List[File]:
        if not file_ids:
            return []
        with self.connect() as (conn, cursor):
            sql_placeholder = ", ".join(["?" for _ in range(len(file_ids))])
            sql = replace_kwargs(queries.select_by_ids, file_ids=sql_placeholder)
            cursor.execute(sql, file_ids)
            rows = cursor.fetchall()
            return [self.parse_row(row) for row in rows]

    def get_file(self, file_id: int) -> File:
        with self.connect() as (conn, cursor):
            cursor.execute(queries.select_by_id, (file_id,))
            rows = cursor.fetchall()
            if len(rows) == 1:
                return self.parse_row(rows[0])
            else:
                raise ApiError(500, "Not Implemented")

    def get_orphaned_files(self) -> List[File]:
        with self.connect() as (conn, cursor):
            cursor.execute(queries.select_orphaned_files)
            rows = cursor.fetchall()
            return [self.parse_row(row) for row in rows]

    def has_orphaned_files(self) -> bool:
        with self.connect() as (conn, cursor):
            cursor.execute(queries.select_orphaned_files)
            rows = cursor.fetchall()
            return len(rows) > 0

    # The following may not work anymore


    def file_has_tag(self, file_id: int, tag_id: int) -> bool:
        with self.connect() as (conn, cursor):
            if not self._file_exists(cursor, file_id):
                raise ApiError(status.HTTP_410_GONE, f"No file found with the given id: '{file_id}'")
            return self._file_tag_exists(cursor, file_id, tag_id)

    def get_file_path(self, file_id: int) -> Optional[str]:
        # Dont need to check; it will raise an DBI error if it fails to get the file
        # Parent functions should handle the error as they need
        file = self.query.get_file(FileQuery(id=file_id, fields=["path"]))
        return file.path
