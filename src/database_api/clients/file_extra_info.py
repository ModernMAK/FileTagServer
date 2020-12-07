from typing import Tuple, List, Dict, Any

from src.database_api.clients.file import FileTable
from src.database_api.clients.shared import AbstractTable
from src.database_api.util import BaseClient, sql_select_from, sql_in, sql_limit, sql_offset, \
    sql_assemble_query, sql_create_table_value, sql_assemble_modifiers, sql_create_table, \
    sql_insert_into, sql_and_clauses, sql_action, sql_on_change, sql_on_action, sql_create_foreign_key


class FileExtraInfoTable(AbstractTable):
    table = "file_extra_info"

    id = 'id'
    file_id = 'file_id'
    hash = 'hash'
    size = 'size'

    id_qualified = AbstractTable.qualify_name(table, id)
    file_id_qualified = AbstractTable.qualify_name(table, file_id)
    hash_qualified = AbstractTable.qualify_name(table, hash)
    size_qualified = AbstractTable.qualify_name(table, size)


class FileExtraInfoClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def _get_mapping() -> Tuple:
        return FileExtraInfoTable.id, FileExtraInfoTable.file_id, FileExtraInfoTable.size, FileExtraInfoTable.hash

    @classmethod
    def get_select_query(cls,
                         limit: int = None, offset: int = None,
                         ids: List[int] = None, files: List[int] = None, hashes: List[str] = None,
                         **kwargs):

        mapping = cls._get_mapping()

        query = sql_select_from(mapping, FileExtraInfoTable.table)
        constraint_clauses = [
            sql_in(f'{FileExtraInfoTable.id_qualified}', ids),
            sql_in(f'{FileExtraInfoTable.file_id_qualified}', files),
            sql_in(f'{FileExtraInfoTable.hash_qualified}', hashes)]

        constraint_clause = sql_and_clauses(constraint_clauses)
        structure_clauses = []

        structure_clauses.append(sql_limit(limit))
        structure_clauses.append(sql_offset(offset))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @classmethod
    def get_create_table_query(cls):
        action_clauses = [
            sql_on_action(sql_on_change(on_update=True), sql_action(cascade=True)),
            sql_on_action(sql_on_change(on_delete=True), sql_action(restrict=True))
        ]
        values = [
            sql_create_table_value(FileExtraInfoTable.id, 'INTEGER', sql_assemble_modifiers(True, True)),

            sql_create_table_value(FileExtraInfoTable.hash, 'BLOB'),
            sql_create_table_value(FileExtraInfoTable.size, "INTEGER"),

            sql_create_table_value(FileExtraInfoTable.file_id, "INTEGER"),

            sql_create_foreign_key(FileExtraInfoTable.file_id, FileTable.table, FileTable.id, action_clauses),
        ]
        return sql_create_table(FileExtraInfoTable.table, values)

    def create(self):
        print("Create fei")
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = self._get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = None, **kwargs) -> Dict[Any, Dict[str, Any]]:
        if key is None:
            key = FileTable.id
        query = self.get_select_query(**kwargs)
        mapping = self._get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)

    def insert(self, values: List[Tuple[int, str, int]]):
        query = sql_insert_into(FileExtraInfoTable.table,
                                [FileExtraInfoTable.file_id, FileExtraInfoTable.hash, FileExtraInfoTable.size],
                                values)
        self._execute(query)
