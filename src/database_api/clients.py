from typing import List, Any, Dict, Tuple
from src.database_api.util import *


class FileClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def _get_mapping() -> Tuple:
        return 'id', 'name', 'description', 'path', 'mime'

    @classmethod
    def get_select_query(cls, **kwargs):
        """
        Keyword Args
            limit       ~ # of items to select
            offset      ~ # to offset selection
            order_by    ~ key-value pairs to order by; (name, ascending)
            ids         ~ list of ids to fetch
            paths       ~ list of ids to fetch
            mimes       ~ list of ids to fetch
            mime_likes -> list of
        """
        mapping = cls._get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)

        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        paths = kwargs.get('paths', None)
        mimes = kwargs.get('mimes', None)
        mime_likes = kwargs.get('mime_likes', None)
        name_likes = kwargs.get('name_likes', None)
        desc_likes = kwargs.get('desc_likes', None)

        query = sql_select_from(mapping, 'file')
        constraint_clauses = [
            sql_in('file.id', ids),
            sql_in('file.path', paths),
            sql_in('file.mime', mimes),
            sql_in_like('file.mime', mime_likes),
            sql_in_like('file.name', name_likes),
            sql_in_like('file.description', desc_likes)
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

            sql_create_table_value('path', 'TEXT'),
            sql_create_table_value('mime', "TINYTEXT"),

            sql_create_table_value('name', "TINYTEXT"),
            sql_create_table_value('description', 'TEXT'),

            sql_create_unique_value('path_unique', ['path'])
        ]
        return sql_create_table('file', values)

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

    def fetch_lookup(self, key: str = 'id', **kwargs) -> Dict[Any, Dict[str, Any]]:
        """
            Returns a lookup table, if two items have the same key, the last one processed is used.
            Each element is formatted as such:
                id      ~ the file's internal id
                name    ~ the display name for the file
                description    ~ the description for the file
                path    ~ the local path to the file
                mime    ~ the mimetype of the file
        """
        query = self.get_select_query(**kwargs)
        mapping = self._get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)

    def insert(self, values: List[Tuple[str, str, str, str]]):
        query = sql_insert_into('file', ['path', 'mime', 'name', 'description'], values)
        self._execute(query)


class TagClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'name', 'description', 'count'

    @staticmethod
    def get_select_query(**kwargs):
        mapping = TagClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('name', False)])
        ids = kwargs.get('ids', None)
        names = kwargs.get('names', None)
        desc_likes = kwargs.get('descriptions', None)

        # This query essentially creates a temporary 'tag' table with a tag counts column
        # we dont use any of my sql hoodoo helpers because thats mostly for
        inner_query = "select tag.id, tag.name, tag.description, count(file_tag.file_id) as count from tag" \
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


class FileTagMapClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'file_id', 'tag_id'

    @staticmethod
    def get_select_query(**kwargs):
        mapping = FileTagMapClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        group_by = kwargs.get('group_by', None)
        ids = kwargs.get('ids', None)
        files = kwargs.get('files', None)
        tags = kwargs.get('tags', None)

        query = sql_select_from(mapping, 'file_tag')
        constraint_clauses = [
            sql_in('file_tag.id', ids),
            sql_in('file_tag.file_id', files),
            sql_in('file_tag.tag_id', tags),
        ]

        constraint_clause = sql_and_clauses(constraint_clauses)

        structure_clauses = []

        if group_by:
            for name in group_by:
                structure_clauses.append(sql_group_by(name))

        for (name, asc) in order_by:
            structure_clauses.append(sql_order_by(name, asc))
        structure_clauses.append(sql_limit(limit))
        structure_clauses.append(sql_offset(offset))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @staticmethod
    def get_create_table_query():
        action_clauses = [
            sql_on_action(sql_on_change(on_update=True), sql_action(cascade=True)),
            sql_on_action(sql_on_change(on_delete=True), sql_action(restrict=True))
        ]
        values = [
            sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
            sql_create_table_value('file_id', 'INTEGER'),
            sql_create_table_value('tag_id', "INTEGER"),
            sql_create_unique_value('pair_u', ['file_id', 'tag_id']),
            sql_create_foreign_key('file_id', 'file', 'id', action_clauses),
            sql_create_foreign_key('tag_id', 'tag', 'id', action_clauses)
        ]
        return sql_create_table('file_tag', values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = 'id', **kwargs) -> LookupQueryResult:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def fetch_lookup_groups(self, key: str = 'id', **kwargs) -> LookupGroupsQueryResult:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_lookup_groups(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)


class MasterClient:
    def __init__(self, **kwargs):
        db_path = kwargs.get('db_path')
        self.file = FileClient(db_path=db_path)
        self.tag = TagClient(db_path=db_path)
        self.map = FileTagMapClient(db_path=db_path)

    def create_all(self):
        self.file.create()
        self.tag.create()
        self.map.create()
