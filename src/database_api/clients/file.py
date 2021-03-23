import sqlite3
from sqlite3 import Cursor, Row
from typing import Tuple, List, Dict, Any, Iterable

from src.database_api.clients.shared import AbstractTable
from src.database_api.util import BaseClient, sql_select_from, sql_in, sql_in_like, sql_order_by, sql_limit, sql_offset, \
    sql_assemble_query, sql_create_table_value, sql_assemble_modifiers, sql_create_unique_value, sql_create_table, \
    sql_insert_into, sql_and_clauses
from sqlite3 import Cursor


class SqlHelper:
    @staticmethod
    def read_sql_file(file: str):
        with open(file) as f:
            return f.read()

    @staticmethod
    def file_execute(cursor: Cursor, file: str, params: Iterable = None):
        with open(file) as f:
            query = f.read()
            cursor.execute(query, params)

    @staticmethod
    def file_execute_many(cursor: Cursor, file: str, params: Iterable = None):
        with open(file) as f:
            query = f.read()
            cursor.executemany(query, params)

    class File:
        @staticmethod
        def create(cursor: Cursor):
            SqlHelper.file_execute(cursor, "/sql/file/create.sql")

        @staticmethod
        def insert(cursor: Cursor, params: Iterable):
            SqlHelper.file_execute(cursor, "/sql/file/insert.sql", params)

        @staticmethod
        def insert_many(cursor: Cursor, params: Iterable):
            SqlHelper.file_execute_many(cursor, "/sql/file/insert.sql", params)




# class FileClient(BaseClient):
#     @classmethod
#     def get_select_query(cls,
#                          limit: int = None, offset: int = None,
#                          ids: List[int] = None, paths: List[str] = None, mimes: List[str] = None,
#                          mime_likes: List[int] = None, name_likes: List[str] = None, desc_likes: List[str] = None,
#                          order_by: List[Tuple[str, bool]] = None,
#                          **kwargs):
#
#         mapping = cls._get_mapping()
#
#         if order_by is None:
#             order_by = [('id', True)]
#
#         query = sql_select_from(mapping, FileTable.table)
#         constraint_clauses = [
#             sql_in(f'{FileTable.id_qualified}', ids),
#             sql_in(f'{FileTable.path_qualified}', paths),
#             sql_in(f'{FileTable.mimetype_qualified}', mimes),
#             sql_in_like(f'{FileTable.mimetype_qualified}', mime_likes),
#             sql_in_like(f'{FileTable.name_qualified}', name_likes),
#             sql_in_like(f'{FileTable.description_qualified}', desc_likes)
#         ]
#
#         constraint_clause = sql_and_clauses(constraint_clauses)
#         structure_clauses = []
#         for (name, asc) in order_by:
#             structure_clauses.append(sql_order_by(name, asc))
#         structure_clauses.append(sql_limit(limit))
#         structure_clauses.append(sql_offset(offset))
#
#         return sql_assemble_query(query, constraint_clause, structure_clauses)
#