from typing import List, Any, Dict

from src.database.util import *


class PageClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'name', 'description'

    @staticmethod
    def get_select_query(**kwargs):
        mapping = PageClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        names = kwargs.get('names', None)
        desc_likes = kwargs.get('desc', None)

        query = sql_select_from(mapping, 'page')
        constraint_clauses = [
            sql_in('page.id', ids),
            sql_in('page.name', names),
            sql_in_like('page.description', desc_likes)
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
            sql_create_table_value('name', 'TINYTEXT'),
            sql_create_table_value('description', "TEXT"),
            sql_create_unique_value('name_unique', ['name'])
        ]
        return sql_create_table('page', values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = PageClient.get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = 'id', **kwargs) -> Dict[Any, Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = PageClient.get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)
