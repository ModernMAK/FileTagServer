# from typing import Tuple, List, Dict, Any
#
# from src.database_api.clients.shared import AbstractTable
# from src.database_api.util import BaseClient, sql_select_from, sql_in, sql_in_like, sql_order_by, sql_limit, sql_offset, \
#     sql_assemble_query, sql_create_table_value, sql_assemble_modifiers, sql_create_unique_value, sql_create_table, \
#     sql_insert_into, sql_and_clauses, sql_group_by, sql_on_action, sql_on_change, sql_action, sql_create_foreign_key, \
#     LookupQueryResult, LookupGroupsQueryResult
#
#
# class FileTagMapTable(AbstractTable):
#     table = "file_tag"
#
#     id = 'id'
#     file_id = 'file_id'
#     tag_id = 'tag_id'
#
#     id_qualified = AbstractTable.qualify_name(table, id)
#     file_id_qualified = AbstractTable.qualify_name(table, file_id)
#     tag_id_qualified = AbstractTable.qualify_name(table, tag_id)
#
#
# class FileTagMapClient(BaseClient):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#     @staticmethod
#     def get_mapping() -> Tuple:
#         return 'id', 'file_id', 'tag_id'
#
#     @staticmethod
#     def get_select_query(ids: List[int] = None, **kwargs):
#         mapping = FileTagMapClient.get_mapping()
#         limit = kwargs.get('limit', None)
#         offset = kwargs.get('offset', None)
#         order_by = kwargs.get('order_by', [('id', True)])
#         group_by = kwargs.get('group_by', None)
#         files = kwargs.get('files', None)
#         tags = kwargs.get('tags', None)
#
#         query = sql_select_from(mapping, 'file_tag')
#         constraint_clauses = [
#             sql_in('file_tag.id', ids),
#             sql_in('file_tag.file_id', files),
#             sql_in('file_tag.tag_id', tags),
#         ]
#
#         constraint_clause = sql_and_clauses(constraint_clauses)
#
#         structure_clauses = []
#
#         if group_by:
#             for name in group_by:
#                 structure_clauses.append(sql_group_by(name))
#
#         for (name, asc) in order_by:
#             structure_clauses.append(sql_order_by(name, asc))
#         structure_clauses.append(sql_limit(limit))
#         structure_clauses.append(sql_offset(offset))
#
#         return sql_assemble_query(query, constraint_clause, structure_clauses)
#
#     @staticmethod
#     def get_create_table_query():
#         action_clauses = [
#             sql_on_action(sql_on_change(on_update=True), sql_action(cascade=True)),
#             sql_on_action(sql_on_change(on_delete=True), sql_action(restrict=True))
#         ]
#         values = [
#             sql_create_table_value('id', 'INTEGER', sql_assemble_modifiers(True, True)),
#             sql_create_table_value('file_id', 'INTEGER'),
#             sql_create_table_value('tag_id', "INTEGER"),
#             sql_create_unique_value('pair_u', ['file_id', 'tag_id']),
#             sql_create_foreign_key('file_id', 'file', 'id', action_clauses),
#             sql_create_foreign_key('tag_id', 'tag', 'id', action_clauses)
#         ]
#         return sql_create_table('file_tag', values)
#
#     def create(self):
#         query = self.get_create_table_query()
#         return self._execute(query)
#
#     def fetch(self, **kwargs) -> List[Dict[str, Any]]:
#         query = self.get_select_query(**kwargs)
#         mapping = self.get_mapping()
#         return self._fetch_all_mapped(query, mapping)
#
#     def fetch_lookup(self, key: str = 'id', **kwargs) -> LookupQueryResult:
#         query = self.get_select_query(**kwargs)
#         mapping = self.get_mapping()
#         return self._fetch_all_lookup(query, mapping, key)
#
#     def fetch_lookup_groups(self, key: str = 'id', **kwargs) -> LookupGroupsQueryResult:
#         query = self.get_select_query(**kwargs)
#         mapping = self.get_mapping()
#         return self._fetch_all_lookup_groups(query, mapping, key)
#
#     def __internal_get_simplified_lookup(self, primary_key:str, lookup_key:str, files:List[int]=None, tags:List[int]=None):
#         query = self.get_select_query(files=files,tags=tags)
#         mapping = self.get_mapping()
#         results = self._fetch_all_lookup_groups(query, mapping, primary_key)
#         lookup = {}
#         for key, value in results.items():
#             lookup[key] = [row[lookup_key] for row in value]
#         return lookup
#
#     def __internal_get_unique(self,  primary_key:str,files:List[int]=None,tags:List[int]=None) -> List[int]:
#         results = self.fetch_lookup_groups(key=primary_key, files=files,tags=tags)
#         unique = [result for result in results]
#         return unique
#
#     def get_file2tag_lookup(cls, file_ids: List[int] = None) -> Dict[int, List[int]]:
#         return cls.__internal_get_simplified_lookup(FileTagMapTable.file_id, FileTagMapTable.tag_id, files=file_ids)
#
#     def get_tag2file_lookup(cls, tag_ids: List[int] = None) -> Dict[int, List[int]]:
#         return cls.__internal_get_simplified_lookup( FileTagMapTable.tag_id, FileTagMapTable.file_id,tags=tag_ids)
#
#     def get_unique_tags_from_files(cls, file_ids: List[int] = None) -> List[int]:
#         return cls.__internal_get_unique(FileTagMapTable.file_id,files=file_ids)
#
#     def get_unique_files_from_tags(cls, tag_ids: List[int] = None) -> List[int]:
#         return cls.__internal_get_unique(FileTagMapTable.tag_id,tags=tag_ids)
#
#     def count(self, **kwargs) -> int:
#         query = self.get_select_query(**kwargs)
#         return self._count(query)
