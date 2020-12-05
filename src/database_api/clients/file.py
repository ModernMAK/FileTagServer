from typing import Tuple, List, Dict, Any

from src.database_api.clients.shared import AbstractTable
from src.database_api.util import BaseClient, sql_select_from, sql_in, sql_in_like, sql_order_by, sql_limit, sql_offset, \
    sql_assemble_query, sql_create_table_value, sql_assemble_modifiers, sql_create_unique_value, sql_create_table, \
    sql_insert_into, sql_and_clauses


class FileTable(AbstractTable):
    table = "file"

    id = 'id'
    name = 'name'
    description = 'description'
    path = 'path'
    mimetype = 'mime'

    id_qualified = AbstractTable.qualify_name(table, id)
    name_qualified = AbstractTable.qualify_name(table, name)
    description_qualified = AbstractTable.qualify_name(table, description)
    path_qualified = AbstractTable.qualify_name(table, path)
    mimetype_qualified = AbstractTable.qualify_name(table, mimetype)


class FileClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def _get_mapping() -> Tuple:
        return 'id', 'name', 'description', 'path', 'mime'

    @classmethod
    def get_select_query(cls,
                         limit: int = None, offset: int = None,
                         ids: List[int] = None, paths: List[str] = None, mimes: List[str] = None,
                         mime_likes: List[int] = None, name_likes: List[str] = None, desc_likes: List[str] = None,
                         order_by: List[Tuple[str, bool]] = None,
                         **kwargs):

        mapping = cls._get_mapping()

        if order_by is None:
            order_by = [('id', True)]

        query = sql_select_from(mapping, FileTable.table)
        constraint_clauses = [
            sql_in(f'{FileTable.id_qualified}', ids),
            sql_in(f'{FileTable.path_qualified}', paths),
            sql_in(f'{FileTable.mimetype_qualified}', mimes),
            sql_in_like(f'{FileTable.mimetype_qualified}', mime_likes),
            sql_in_like(f'{FileTable.name_qualified}', name_likes),
            sql_in_like(f'{FileTable.description_qualified}', desc_likes)
        ]

        constraint_clause = sql_and_clauses(constraint_clauses)
        structure_clauses = []
        for (name, asc) in order_by:
            structure_clauses.append(sql_order_by(name, asc))
        structure_clauses.append(sql_limit(limit))
        structure_clauses.append(sql_offset(offset))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @classmethod
    def get_create_table_query(cls):
        values = [
            sql_create_table_value(FileTable.id, 'INTEGER', sql_assemble_modifiers(True, True)),

            sql_create_table_value(FileTable.path, 'TEXT'),
            sql_create_table_value(FileTable.mimetype, "TINYTEXT"),

            sql_create_table_value(FileTable.name, "TINYTEXT"),
            sql_create_table_value(FileTable.description, 'TEXT'),

            sql_create_unique_value(f'{FileTable.path}_unique', ['path'])
        ]
        return sql_create_table(FileTable.table, values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
            Returns a list, each element is formatted as such:
                id          ~ the file's internal id
                name        ~ the display name for the file
                description ~ the description for the file
                path        ~ the local path to the file
                mime        ~ the mimetype of the file
        """

        query = self.get_select_query(**kwargs)
        mapping = self._get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = None, **kwargs) -> Dict[Any, Dict[str, Any]]:
        """
            Returns a lookup table, if two items have the same key, the last one processed is used.
            Each element is formatted as such:
                id      ~ the file's internal id
                name    ~ the display name for the file
                description    ~ the description for the file
                path    ~ the local path to the file
                mime    ~ the mimetype of the file
        """
        if key is None:
            key = FileTable.id
        query = self.get_select_query(**kwargs)
        mapping = self._get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)

    def insert(self, values: List[Tuple[str, str, str, str]]):
        query = sql_insert_into(FileTable.table,
                                [FileTable.path, FileTable.mimetype, FileTable.name, FileTable.description],
                                values)
        self._execute(query)
