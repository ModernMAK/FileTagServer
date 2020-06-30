# import sqlite3
#
# from typing import Dict, Union, List, Tuple
#
# from src.DbUtil import Conwrapper, create_entry_string, create_value_string, sanitize
# from src.API.Models import ImageModel, TagModel
#
#
# def tuple_to_dict(value: Union[None, Tuple, List[Tuple]], mapping: Union[Tuple, List]):
#     if value is None:
#         return {}
#     if not isinstance(value, List):
#         result = {}
#         for i in range(len(mapping)):
#             v = value[i]
#             m = mapping[i]
#             result[m] = v
#         return result
#     else:
#         result = []
#         for row in value:
#             temp = {}
#             for i in range(len(mapping)):
#                 v = row[i]
#                 m = mapping[i]
#                 temp[m] = v
#             result.append(temp)
#         return result
#
#
# # OLD ~ reusable if we just update references
# class ApiClient:
#     def __init__(self, db_path: str):
#         self.db_path = db_path
#         self.image_client = ImageClient(db_path)
#         self.tag_client = TagClient(db_path)
#
#
# class BaseClient:
#     def __init__(self, **kwargs):
#         self.db_path = kwargs.get('db_path')
#
#     def _perform_select(self, select_query: str):
#         try:
#             with Conwrapper(self.db_path) as (con, cursor):
#                 cursor.execute(select_query)
#                 return cursor.fetchall()
#         except sqlite3.DatabaseError:
#             return None
#
#
# class FileClient(BaseClient):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         mapping = ("id", "path", "extension")
#         return tuple_to_dict(result, mapping)
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get(self, **kwargs):
#         allowed_ids = kwargs.get('ids', None)
#         allowed_paths = kwargs.get('paths', None)
#         allowed_extensions = kwargs.get('exts', None)
#         page_size = kwargs.get('page_size', None)
#         page_offset = kwargs.get('page_offset', None)
#
#         # Assemble a query
#         query = f"SELECT id, path, extension from file"
#         if allowed_ids is not None or allowed_paths is not None or allowed_extensions is not None:
#             query += f" where"
#             require_or = False
#             if allowed_ids is not None:
#                 query += f" id in {create_entry_string(allowed_ids)}"
#                 require_or = True
#             if allowed_paths is not None:
#                 if require_or:
#                     query += f" or"
#                 query += f" path in {create_entry_string(allowed_paths)}"
#                 require_or = True
#             if allowed_extensions is not None:
#                 if require_or:
#                     query += f" or"
#                 query += f" path in {create_entry_string(allowed_extensions)}"
#                 require_or = True
#             if page_size is not None:
#                 query += f" LIMIT {int(page_size)}"
#             if page_offset is not None:
#                 query += f" OFFSET {int(page_offset)}"
#         return self._perform_select(query)
#
#
# class ImageFileClient(BaseClient):
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         mapping = ("id", "path", "extension", "width", "height")
#         return tuple_to_dict(result, mapping)
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get(self, **kwargs):
#         allowed_ids = kwargs.get('ids', None)
#         allowed_file_ids = create_entry_string(kwargs.get('file_ids', None))
#         min_width = kwargs.get('min_width', None)
#         max_width = kwargs.get('max_width', None)
#         min_height = kwargs.get('min_height', None)
#         max_height = kwargs.get('max_height', None)
#         page_size = kwargs.get('page_size', None)
#         page_offset = kwargs.get('page_offset', None)
#
#         # Assemble a query
#         query = f"SELECT id, file_id, width, height from image_file"
#         if any(v is not None for v in [allowed_file_ids, allowed_ids, min_height, min_width, max_width, max_height]):
#             query += f" where"
#             require_or = False
#             if allowed_ids is not None:
#                 query += f" id in {create_entry_string(allowed_ids)}"
#                 require_or = True
#             if allowed_file_ids is not None:
#                 if require_or:
#                     query += f" or"
#                 query += f" file_id in {create_entry_string(allowed_file_ids)}"
#                 require_or = True
#
#             if min_width is not None or max_width is not None:
#                 if require_or:
#                     query += f" or"
#                 if min_width is not None and max_width is not None:
#                     query += f" width between {int(min_width)} and {int(max_width)}"
#                 elif min_width is not None:
#                     query += f" width > {int(min_width)}"
#                 else:
#                     query += f" width < {int(max_width)}"
#                 require_or = True
#
#             if min_height is not None or max_height is not None:
#                 if require_or:
#                     query += f" or"
#                 if min_width is not None and max_width is not None:
#                     query += f" height between {int(min_height)} and {int(max_height)}"
#                 elif min_width is not None:
#                     query += f" height > {int(min_height)}"
#                 else:
#                     query += f" height < {int(max_height)}"
#                 require_or = True
#             if page_size is not None:
#                 query += f" LIMIT {int(page_size)}"
#             if page_offset is not None:
#                 query += f" OFFSET {int(page_offset)}"
#         return self._perform_select(query)
#
#
# class ImageMipClient(BaseClient):
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         mapping = ("id", "path", "extension", "width", "height", "map_id", "name", "scale")
#         return tuple_to_dict(result, mapping)
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get_all(self):
#         query = f"SELECT image_mip.id, path, extension, width, height, map_id, name, scale from image_mip" \
#                 f" left join image_file on image_mip.image_id = image_file.id" \
#                 f" left join file on image_file.file_id = file.id"
#         return self._perform_select(query)
#
#     def get_paged(self, page_size: int = 50, page_offset: int = 0):
#         query = f"SELECT image_mip.id, path, extension, width, height, map_id, name, scale from image_mip" \
#                 f" left join image_file on image_mip.image_id = image_file.id" \
#                 f" left join file on image_file.file_id = file.id" \
#                 f" LIMIT {page_size} OFFSET {page_offset}"
#         return self._perform_select(query)
#
#     def get(self, **kwargs):
#         allowed_ids = create_entry_string(kwargs.get('ids', []))
#         allowed_map_ids = create_entry_string(kwargs.get('map_ids', []))
#         allowed_file_ids = create_entry_string(kwargs.get('file_ids', []))
#         allowed_image_ids = create_entry_string(kwargs.get('image_ids', []))
#         allowed_paths = create_entry_string(kwargs.get('paths', []))
#         allowed_extensions = create_entry_string(kwargs.get('exts', []))
#         query = f"SELECT image_mip.id, path, extension, width, height, map_id, name, scale from image_mip" \
#                 f" left join image_file on image_mip.image_id = image_file.id" \
#                 f" left join file on image_file.file_id = file.id" \
#                 f" where image_mip.id in {allowed_ids} or file.id in {allowed_file_ids}" \
#                 f" or image_file.id in {allowed_image_ids} or path in {allowed_paths}" \
#                 f" or extension in {allowed_extensions} or map_id in {allowed_map_ids}"
#         return self._perform_select(query)
#
#
# class ImageMipmapClient(BaseClient):
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         mapping = ("map_id", "path", "extension", "width", "height", "id", "name", "scale")
#         ungrouped = tuple_to_dict(result, mapping)
#         grouped = {}
#         for row in ungrouped:
#             map_id = row['map_id']
#             if map_id in grouped:
#                 grouped[map_id].append(row)
#             else:
#                 grouped[map_id] = [row]
#
#         formatted = []
#         for k, v in grouped.items():
#             temp = {
#                 'id': k,
#                 'mips': v
#             }
#             formatted.append(temp)
#         return formatted
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get_all(self):
#         query = f"SELECT image_mipmap.id, path, extension, width, height, image_mip.id as mip_id, name, scale from image_mipmap" \
#                 f" left join image_mip on image_mip.map_id = image_mipmap.id" \
#                 f" left join image_file on image_mip.image_id = image_file.id" \
#                 f" left join file on image_file.file_id = file.id"
#         return self._perform_select(query)
#
#     def get_paged(self, page_size: int = 50, page_offset: int = 0):
#         query = f"SELECT image_mipmap.id, path, extension, width, height, image_mip.id as mip_id, name, scale from image_mipmap" \
#                 f" left join image_mip on image_mip.map_id = image_mipmap.id" \
#                 f" left join image_file on image_mip.image_id = image_file.id" \
#                 f" left join file on image_file.file_id = file.id" \
#                 f" LIMIT {page_size} OFFSET {page_offset}"
#         return self._perform_select(query)
#
#     def get(self, **kwargs):
#         allowed_ids = create_entry_string(kwargs.get('ids', []))
#         query = f"SELECT image_mipmap.id, path, extension, width, height, image_mip.id as mip_id, name, scale from image_mipmap" \
#                 f" left join image_mip on image_mip.map_id = image_mipmap.id" \
#                 f" left join image_file on image_mip.image_id = image_file.id" \
#                 f" left join file on image_file.file_id = file.id" \
#                 f" where image_mipmap.id in {allowed_ids}"
#         return self._perform_select(query)
#
#
# class TagClient(BaseClient):
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         mapping = ("id", "name", "description", "class", "count")
#         return tuple_to_dict(result, mapping)
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get_all(self):
#         query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
#                 f" left join tag_map on tag.id = tag_map.tag_id group by tag.id"
#         return self._perform_select(query)
#
#     def get_paged(self, page_size: int = 50, page_offset: int = 0):
#         query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
#                 f" left join tag_map on tag.id = tag_map.tag_id group by tag.id" \
#                 f" LIMIT {page_size} OFFSET {page_offset}"
#
#         return self._perform_select(query)
#
#     def get(self, **kwargs):
#         allowed_ids = create_entry_string(kwargs.get('ids', []))
#         allowed_names = create_entry_string(kwargs.get('names', []))
#         allowed_classes = create_entry_string(kwargs.get('classes', []))
#         query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
#                 f" left join tag_map on tag.id = tag_map.tag_id" \
#                 f" where tag.id in {allowed_ids} or name in {allowed_names} or class in {allowed_classes}" \
#                 f" group by tag.id"
#         return self._perform_select(query)
#
#
# class PostClient(BaseClient):
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         # post.id, post.name, post.description, tag_id, tag_name,tag_class, tag_count
#         mapping = ("id", "name", "description", "tag_id", "tag_name", "tag_class", "tag_count", "tag_description")
#         ungrouped = tuple_to_dict(result, mapping)
#         grouped = {}
#         for row in ungrouped:
#             post_id = row['id']
#             tag = {
#                 'id': row['tag_id'],
#                 'name': row['tag_name'],
#                 'description': row['tag_description'],
#                 'class': row['tag_class'],
#                 'count': row['tag_count'],
#             }
#             if post_id in grouped:
#                 grouped[post_id]['tags'].append(row)
#             else:
#                 grouped[post_id] = {
#                     'id': post_id,
#                     'name': row['name'],
#                     'description': row['description'],
#                     'tags': [tag]
#                 }
#         formatted = []
#         for _, v in grouped.items():
#             formatted.append(v)
#         return formatted
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get_all(self):
#         query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name, " \
#                 f"tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
#                 f" left join tag_map on post.id = tag_map.post_id" \
#                 f" left join tag on tag.id = tag_map.tag_id"
#         return self._perform_select(query)
#
#     def get_paged(self, page_size: int = 50, page_offset: int = 0):
#         query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
#                 f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
#                 f" left join tag_map on post.id = tag_map.post_id" \
#                 f" left join tag on tag.id = tag_map.tag_id" \
#                 f" LIMIT {page_size} OFFSET {page_offset}"
#
#         return self._perform_select(query)
#
#     def get(self, **kwargs):
#         allowed_ids = create_entry_string(kwargs.get('ids', []))
#         allowed_names = create_entry_string(kwargs.get('names', []))
#         query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
#                 f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
#                 f" left join tag_map on post.id = tag_map.post_id" \
#                 f" left join tag on tag.id = tag_map.tag_id" \
#                 f" where post.id in {allowed_ids} or post.name in {allowed_names}"
#         return self._perform_select(query)
#
#
# class ImagePostClient(BaseClient):
#     def __format_result(self, result: Union[Tuple, List[Tuple]]):
#         # post.id, post.name, post.description, tag_id, tag_name,tag_class, tag_count
#         mapping = ("id", "name", "description", "tag_id", "tag_name", "tag_class", "tag_count", "tag_description")
#         ungrouped = tuple_to_dict(result, mapping)
#         grouped = {}
#         for row in ungrouped:
#             post_id = row['id']
#             tag = {
#                 'id': row['tag_id'],
#                 'name': row['tag_name'],
#                 'description': row['tag_description'],
#                 'class': row['tag_class'],
#                 'count': row['tag_count'],
#             }
#             if post_id in grouped:
#                 grouped[post_id]['tags'].append(row)
#             else:
#                 grouped[post_id] = {
#                     'id': post_id,
#                     'name': row['name'],
#                     'description': row['description'],
#                     'tags': [tag]
#                 }
#         formatted = []
#         for _, v in grouped.items():
#             formatted.append(v)
#         return formatted
#
#     def _perform_select(self, select_query: str):
#         result = super()._perform_select(select_query)
#         return self.__format_result(result)
#
#     def get_all(self):
#         query = f"SELECT image_post.id, post.id as post_id, post.name, post.description, tag.id as tag_id, tag.name as tag_name, " \
#                 f"tag.class as tag_class, count(image_post.post_id) as tag_count, tag.description as tag_description from image_post" \
#                 f" left join post on post.id = image_post.post_id" \
#                 f" left join tag_map on post.id = tag_map.post_id" \
#                 f" left join tag on tag.id = tag_map.tag_id"
#         return self._perform_select(query)
#
#     def get_paged(self, page_size: int = 50, page_offset: int = 0):
#         query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
#                 f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
#                 f" left join tag_map on post.id = tag_map.post_id" \
#                 f" left join tag on tag.id = tag_map.tag_id" \
#                 f" LIMIT {page_size} OFFSET {page_offset}"
#
#         return self._perform_select(query)
#
#     def get(self, **kwargs):
#         allowed_ids = create_entry_string(kwargs.get('ids', []))
#         allowed_names = create_entry_string(kwargs.get('names', []))
#         query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
#                 f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
#                 f" left join tag_map on post.id = tag_map.post_id" \
#                 f" left join tag on tag.id = tag_map.tag_id" \
#                 f" where post.id in {allowed_ids} or post.name in {allowed_names}"
#         return self._perform_select(query)
