from typing import List, Any, Dict

from src.database.util import *


class FileClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'path', 'mime'

    @staticmethod
    def get_select_query(**kwargs):
        mapping = FileClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        paths = kwargs.get('paths', None)
        mimes = kwargs.get('mimes', None)
        mime_likes = kwargs.get('mime_likes', None)

        query = sql_select_from(mapping, 'file')
        constraint_clauses = [
            sql_in('file.id', ids),
            sql_in('file.path', paths),
            sql_in('file.mime', mimes),
            sql_in_like('file.mime', mime_likes)
        ]

        constraint_clause = sql_and_clauses(constraint_clauses)
        structure_clauses = [
            sql_limit(limit),
            sql_offset(offset),
        ]
        for (name, asc) in order_by:
            structure_clauses.append(sql_order_by(name, asc))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @staticmethod
    def get_create_table_query():
        values = [
            sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
            sql_create_table_value('path', 'TEXT'),
            sql_create_table_value('mime', "TINYTEXT"),
            sql_create_unique_value('path_unique', ['path'])
        ]
        return sql_create_table('file', values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = FileClient.get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = 'id', **kwargs) -> Dict[Any, Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = FileClient.get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)
