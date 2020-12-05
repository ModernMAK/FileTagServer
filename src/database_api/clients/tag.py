from typing import Tuple, List, Dict, Any

from src.database_api.clients.shared import AbstractTable
from src.database_api.util import BaseClient, sql_select_from, sql_in, sql_in_like, sql_order_by, sql_limit, sql_offset, \
    sql_assemble_query, sql_create_table_value, sql_assemble_modifiers, sql_create_unique_value, sql_create_table, \
    sql_and_clauses


class TagTable(AbstractTable):
    table = "tag"

    id = 'id'
    name = 'name'
    description = 'description'
    count = 'count'

    id_qualified = AbstractTable.qualify_name(table, id)
    name_qualified = AbstractTable.qualify_name(table, name)
    description_qualified = AbstractTable.qualify_name(table, description)
    count_qualified = AbstractTable.qualify_name(table, count)


class TagClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    table_name = 'tag'
    id_column = 'id'
    name_column = 'name'
    desc_column = 'description'
    count_column = 'count'

    @classmethod
    def _prefixed_column(cls, col):
        return f"{cls.table_name}.{col}"

    @classmethod
    def get_mapping(cls) -> Tuple:
        return cls.id_column, cls.name_column, cls.desc_column, cls.count_column

    @classmethod
    def get_select_query(cls, **kwargs):
        mapping = TagClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('name', False)])
        ids = kwargs.get('ids', None)
        names = kwargs.get('names', None)
        desc_likes = kwargs.get('descriptions', None)

        # This query essentially creates a temporary 'tag' table with a tag counts column
        # we dont use any of my sql hoodoo helpers because thats mostly for
        inner_query = f"select {cls._prefixed_column(cls.id_column)}, {cls._prefixed_column(cls.name_column)}, {cls._prefixed_column(cls.desc_column)}, count(file_tag.file_id) as count from tag" \
                      " left join file_tag on tag.id = file_tag.tag_id" \
                      " group by tag.id"

        # This query then selects from our temporary 'tag' table
        query = sql_select_from(mapping, inner_query, inner_query=True)
        constraint_clauses = [
            sql_in('id', ids),
            sql_in('name', names),
            sql_in_like('description', desc_likes),

        ]

        constraint_clause = sql_and_clauses(constraint_clauses)
        structure_clauses = []
        for (name, asc) in order_by:
            structure_clauses.append(sql_order_by(name, asc))
        structure_clauses.append(sql_limit(limit))
        structure_clauses.append(sql_offset(offset))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @staticmethod
    def get_create_table_query():
        values = [
            sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
            sql_create_table_value('name', 'TINYTEXT'),
            sql_create_table_value('description', "TEXT"),
            sql_create_unique_value('name_u', ['name'])
        ]
        return sql_create_table('tag', values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = TagClient.get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = 'id', **kwargs) -> Dict[Any, Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = TagClient.get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)

    @classmethod
    def id_column_qualified(cls):
        return f"{cls.table_name}.{cls.id_column}"

    @classmethod
    def name_column_qualified(cls):
        pass
