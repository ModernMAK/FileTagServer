from typing import List, Any, Dict
from src.database.util import *


class FileClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'path', 'mime'

    @classmethod
    def get_select_query(cls, **kwargs):
        mapping = cls.get_mapping()
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

    def insert(self, values: List[Tuple[str, str]]):
        query = sql_insert_into('file', ['path', 'mime'], values)
        self._execute(query)


class GeneratedContentClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'file_id'

    @classmethod
    def get_select_query(cls, **kwargs):
        mapping = cls.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        file_ids = kwargs.get('file_ids', None)

        query = sql_select_from(mapping, 'file_page')
        constraint_clauses = [
            sql_in('generated_content.id', ids),
            sql_in('generated_content.file_id', file_ids)
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
        fkey_actions = [
            sql_on_action(sql_on_change(on_update=True), sql_action(cascade=True)),
            sql_on_action(sql_on_change(on_delete=True), sql_action(cascade=True))
        ]
        values = [
            sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
            sql_create_table_value('file_id', 'INTEGER'),
            sql_create_unique_value('file_unique', ['file_id']),
            sql_create_foreign_key('file_id', 'file', 'id', fkey_actions)
        ]
        return sql_create_table('generated_content', values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = 'id', **kwargs) -> Dict[Any, Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)

    def insert(self, values: List[Tuple[int]]):
        query = sql_insert_into('generated_content', ['file_id'], values)
        self._execute(query)


class FileTagClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'file_id', 'tag_id'

    @classmethod
    def get_select_query(cls, **kwargs):
        mapping = cls.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        file_ids = kwargs.get('files', None)
        tag_ids = kwargs.get('tags', None)

        query = sql_select_from(mapping, 'file_tag')
        constraint_clauses = [
            sql_in('file_tag.id', ids),
            sql_in('file_tag.file_id', file_ids),
            sql_in('file_tag.tag_id', tag_ids),
        ]

        constraint_clause = sql_and_clauses(constraint_clauses)
        structure_clauses = [
            sql_limit(limit),
            sql_offset(offset),
        ]
        for (name, asc) in order_by:
            structure_clauses.append(sql_order_by(name, asc))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @classmethod
    def get_tag_count_query(cls, **kwargs):
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        file_ids = kwargs.get('files', None)
        tag_ids = kwargs.get('tags', None)

        query = sql_select_from(["file_tag.tag_id", "COUNT(*) as count"], 'file_tag')
        constraint_clauses = [
            sql_in('file_tag.file_id', file_ids),
            sql_in('file_tag.tag_id', tag_ids),
        ]

        constraint_clause = sql_and_clauses(constraint_clauses)
        structure_clauses = [
            sql_group_by('file_tag.tag_id'),
            sql_limit(limit),
            sql_offset(offset),
        ]
        for (name, asc) in order_by:
            structure_clauses.append(sql_order_by(name, asc))

        return sql_assemble_query(query, constraint_clause, structure_clauses)

    @staticmethod
    def get_create_table_query():

        fkey_actions = [
            sql_on_action(sql_on_change(on_update=True), sql_action(cascade=True)),
            sql_on_action(sql_on_change(on_delete=True), sql_action(restrict=True))
        ]

        values = [
            sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
            sql_create_table_value('file_id', 'INTEGER'),
            sql_create_table_value('tag_id', "INTEGER"),
            sql_create_unique_value('pair_unique', ['file_id', 'tag_id']),
            sql_create_foreign_key('file_id', 'file', 'id', fkey_actions),
            sql_create_foreign_key('tag_id', 'tag', 'id', fkey_actions)
        ]
        return sql_create_table('file_tag', values)

    def create(self):
        query = self.get_create_table_query()
        return self._execute(query)

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_mapped(query, mapping)

    def fetch_lookup(self, key: str = 'id', **kwargs) -> Dict[Any, Dict[str, Any]]:
        query = self.get_select_query(**kwargs)
        mapping = self.get_mapping()
        return self._fetch_all_lookup(query, mapping, key)

    def count(self, **kwargs) -> int:
        query = self.get_select_query(**kwargs)
        return self._count(query)

    def fetch_tag_counts(self, **kwargs) -> Dict[int, Dict[str, Any]]:
        query = self.get_tag_count_query(**kwargs)
        mapping = ["tag_id", 'count']
        return self._fetch_all_lookup(query, mapping, key='tag_id')

    def insert(self, values: List[Tuple[str, str]]):
        query = sql_insert_into('file_tag', ['file_id', 'tag_id'], values)
        self._execute(query)


class FilePageClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'file_id', 'page_id'

    @staticmethod
    def get_select_query(**kwargs):
        mapping = PageClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        file_ids = kwargs.get('file_ids', None)
        page_ids = kwargs.get('page_ids', None)

        query = sql_select_from(mapping, 'file_page')
        constraint_clauses = [
            sql_in('file_page.id', ids),
            sql_in('file_page.file_id', file_ids),
            sql_in('file_page.page_id', page_ids)
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
        fkey_clause = [
            sql_on_action(sql_on_change(on_update=True), sql_action(cascade=True)),
            sql_on_action(sql_on_change(on_delete=True), sql_action(restrict=True))
        ]

        values = [
            sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
            sql_create_table_value('file_id', 'INTEGER'),
            sql_create_table_value('page_id', "INTEGER"),
            sql_create_unique_value('file_id_unique', ['file_id']),
            sql_create_unique_value('page_id_unique', ['page_id']),
            sql_create_foreign_key('file_id', 'file', 'id', fkey_clause),
            sql_create_foreign_key('page_id', 'page', 'id', fkey_clause),
        ]
        return sql_create_table('file_page', values)

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

    def insert(self, values: List[Tuple[int, int]]):
        query = sql_insert_into('file_page', ['file_id', 'page_id'], values)
        self._execute(query)


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

    def insert(self, values: List[Tuple[str, str]]):
        query = sql_insert_into('page', ['name', 'description'], values)
        self._execute(query)


class TagClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_mapping() -> Tuple:
        return 'id', 'name', 'description'

    @staticmethod
    def get_select_query(**kwargs):
        mapping = TagClient.get_mapping()
        limit = kwargs.get('limit', None)
        offset = kwargs.get('offset', None)
        order_by = kwargs.get('order_by', [('id', True)])
        ids = kwargs.get('ids', None)
        names = kwargs.get('names', None)
        desc_likes = kwargs.get('desc', None)

        query = sql_select_from(mapping, 'tag')
        constraint_clauses = [
            sql_in('tag.id', ids),
            sql_in('tag.name', names),
            sql_in_like('tag.description', desc_likes)
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
            sql_create_table_value('description', "TEXT")
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


class FilePageInfoClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_mapping(self):
        return ['id', 'path', 'mime', 'name', 'description']

    def get_select_query(self, **kwargs):
        inner_query = FilePageClient.get_select_query(**kwargs)

        query = f"SELECT file.id, file.path, file.mime, page.name, page.description FROM ({inner_query})" \
                " INNER JOIN file ON file.id = file_page.file_id" \
                " INNER JOIN page ON page.id = file_page.page_id"
        return query

    def fetch(self, **kwargs):
        query = self.get_select_query(**kwargs)
        return self._fetch_all_mapped(query, self._get_mapping())

    def fetch_lookup(self, key='id', **kwargs):
        return self._convert_map_to_lookup(self.fetch(**kwargs), key)


class FileTagInfoClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def _get_mapping():
        return ['file_id', 'tag_id', 'name', 'description', 'count']

    @staticmethod
    def get_select_query(**kwargs):
        inner_query = FileTagClient.get_select_query(**kwargs)
        count_query = f"SELECT file_tag.tag_id, COUNT(*) as count FROM ({inner_query})" \
                      "GROUP BY file_tag.tag_id"

        query = f"SELECT file.id, tag.id, tag.name, tag.description, count FROM ({inner_query})" \
                f" INNER JOIN file ON file.id = file_tag.file_id" \
                f" INNER JOIN tag ON tag.id = file_tag.tag_id" \
                f" INNER JOIN ({count_query}) ON tag.id = file_tag.tag_id"


        return query

    def fetch(self, **kwargs):
        query = self.get_select_query(**kwargs)
        return self._fetch_all_mapped(query, self._get_mapping())

    def fetch_lookup(self, key='file_id', **kwargs):
        return self._convert_map_to_lookup(self.fetch(**kwargs), key)

    def fetch_groups(self, key='file_id', **kwargs):
        return self._convert_map_to_lookup_groups(self.fetch(**kwargs), key)


class FileFullInfoClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fetch(self, **kwargs):
        page_info_mapping = FilePageInfoClient._get_mapping()
        page_info_query = FilePageInfoClient.get_select_query(**kwargs)

        tag_info_mapping = FileTagInfoClient._get_mapping()
        tag_info_query = FileTagInfoClient.get_select_query(**kwargs)

        page_formatted = self._fetch_all_mapped(page_info_query, page_info_mapping)
        tag_formatted = self._fetch_all_mapped(tag_info_query, tag_info_mapping)
        tag_groups = self._convert_map_to_lookup_groups(tag_formatted, 'file_id', drop_key=True)

        for page_info in page_formatted:
            page_info['tags'] = tag_groups[page_info['id']]
        return page_formatted

    def fetch_lookup(self, key='id', **kwargs):
        return self._convert_map_to_lookup(self.fetch(**kwargs), key)


# A helper, just groups all clients into one big class
class MasterClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file = FileClient(**kwargs)
        self.generated_content = GeneratedContentClient(**kwargs)
        self.file_tag_map = FileTagClient(**kwargs)
        self.page = PageClient(**kwargs)
        self.file_page_map = FilePageClient(**kwargs)
        self.file_page_info = FilePageInfoClient(**kwargs)
        self.file_tag_info = FileTagInfoClient(**kwargs)
