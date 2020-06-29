import sqlite3

from typing import Dict, Union, List, Tuple

from src.DbUtil import Conwrapper, create_entry_string, create_value_string, sanitize
from src.API.Models import ImageModel, TagModel


def tuple_to_dict(value: Union[None, Tuple, List[Tuple]], mapping: Union[Tuple, List]):
    if value is None:
        return {}
    if not isinstance(value, List):
        result = {}
        for i in range(len(mapping)):
            v = value[i]
            m = mapping[i]
            result[m] = v
        return result
    else:
        result = []
        for row in value:
            temp = {}
            for i in range(len(mapping)):
                v = row[i]
                m = mapping[i]
                temp[m] = v
            result.append(temp)
        return result


# OLD ~ reusable if we just update references
class ApiClient:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.image_client = ImageClient(db_path)
        self.tag_client = TagClient(db_path)


class BaseClient:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path')

    def _perform_select(self, select_query: str):
        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(select_query)
                return cursor.fetchall()
        except sqlite3.DatabaseError:
            return None


class FileClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        mapping = ("id", "path", "extension")
        return tuple_to_dict(result, mapping)

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get(self, **kwargs):
        allowed_ids = kwargs.get('ids', None)
        allowed_paths = kwargs.get('paths', None)
        allowed_extensions = kwargs.get('exts', None)
        page_size = kwargs.get('page_size', None)
        page_offset = kwargs.get('page_offset', None)

        # Assemble a query
        query = f"SELECT id, path, extension from file"
        if allowed_ids is not None or allowed_paths is not None or allowed_extensions is not None:
            query += f" where"
            require_or = False
            if allowed_ids is not None:
                query += f" id in {create_entry_string(allowed_ids)}"
                require_or = True
            if allowed_paths is not None:
                if require_or:
                    query += f" or"
                query += f" path in {create_entry_string(allowed_paths)}"
                require_or = True
            if allowed_extensions is not None:
                if require_or:
                    query += f" or"
                query += f" path in {create_entry_string(allowed_extensions)}"
                require_or = True
            if page_size is not None:
                query += f" LIMIT {int(page_size)}"
            if page_offset is not None:
                query += f" OFFSET {int(page_offset)}"
        return self._perform_select(query)


class ImageFileClient(BaseClient):
    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        mapping = ("id", "path", "extension", "width", "height")
        return tuple_to_dict(result, mapping)

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get(self, **kwargs):
        allowed_ids = kwargs.get('ids', None)
        allowed_file_ids = create_entry_string(kwargs.get('file_ids', None))
        min_width = kwargs.get('min_width', None)
        max_width = kwargs.get('max_width', None)
        min_height = kwargs.get('min_height', None)
        max_height = kwargs.get('max_height', None)
        page_size = kwargs.get('page_size', None)
        page_offset = kwargs.get('page_offset', None)

        # Assemble a query
        query = f"SELECT id, file_id, width, height from image_file"
        if any(v is not None for v in [allowed_file_ids, allowed_ids, min_height, min_width, max_width, max_height]):
            query += f" where"
            require_or = False
            if allowed_ids is not None:
                query += f" id in {create_entry_string(allowed_ids)}"
                require_or = True
            if allowed_file_ids is not None:
                if require_or:
                    query += f" or"
                query += f" file_id in {create_entry_string(allowed_file_ids)}"
                require_or = True

            if min_width is not None or max_width is not None:
                if require_or:
                    query += f" or"
                if min_width is not None and max_width is not None:
                    query += f" width between {int(min_width)} and {int(max_width)}"
                elif min_width is not None:
                    query += f" width > {int(min_width)}"
                else:
                    query += f" width < {int(max_width)}"
                require_or = True

            if min_height is not None or max_height is not None:
                if require_or:
                    query += f" or"
                if min_width is not None and max_width is not None:
                    query += f" height between {int(min_height)} and {int(max_height)}"
                elif min_width is not None:
                    query += f" height > {int(min_height)}"
                else:
                    query += f" height < {int(max_height)}"
                require_or = True
            if page_size is not None:
                query += f" LIMIT {int(page_size)}"
            if page_offset is not None:
                query += f" OFFSET {int(page_offset)}"
        return self._perform_select(query)


class ImageMipClient(BaseClient):
    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        mapping = ("id", "path", "extension", "width", "height", "map_id", "name", "scale")
        return tuple_to_dict(result, mapping)

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get_all(self):
        query = f"SELECT image_mip.id, path, extension, width, height, map_id, name, scale from image_mip" \
                f" left join image_file on image_mip.image_id = image_file.id" \
                f" left join file on image_file.file_id = file.id"
        return self._perform_select(query)

    def get_paged(self, page_size: int = 50, page_offset: int = 0):
        query = f"SELECT image_mip.id, path, extension, width, height, map_id, name, scale from image_mip" \
                f" left join image_file on image_mip.image_id = image_file.id" \
                f" left join file on image_file.file_id = file.id" \
                f" LIMIT {page_size} OFFSET {page_offset}"
        return self._perform_select(query)

    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_map_ids = create_entry_string(kwargs.get('map_ids', []))
        allowed_file_ids = create_entry_string(kwargs.get('file_ids', []))
        allowed_image_ids = create_entry_string(kwargs.get('image_ids', []))
        allowed_paths = create_entry_string(kwargs.get('paths', []))
        allowed_extensions = create_entry_string(kwargs.get('exts', []))
        query = f"SELECT image_mip.id, path, extension, width, height, map_id, name, scale from image_mip" \
                f" left join image_file on image_mip.image_id = image_file.id" \
                f" left join file on image_file.file_id = file.id" \
                f" where image_mip.id in {allowed_ids} or file.id in {allowed_file_ids}" \
                f" or image_file.id in {allowed_image_ids} or path in {allowed_paths}" \
                f" or extension in {allowed_extensions} or map_id in {allowed_map_ids}"
        return self._perform_select(query)


class ImageMipmapClient(BaseClient):
    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        mapping = ("map_id", "path", "extension", "width", "height", "id", "name", "scale")
        ungrouped = tuple_to_dict(result, mapping)
        grouped = {}
        for row in ungrouped:
            map_id = row['map_id']
            if map_id in grouped:
                grouped[map_id].append(row)
            else:
                grouped[map_id] = [row]

        formatted = []
        for k, v in grouped.items():
            temp = {
                'id': k,
                'mips': v
            }
            formatted.append(temp)
        return formatted

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get_all(self):
        query = f"SELECT image_mipmap.id, path, extension, width, height, image_mip.id as mip_id, name, scale from image_mipmap" \
                f" left join image_mip on image_mip.map_id = image_mipmap.id" \
                f" left join image_file on image_mip.image_id = image_file.id" \
                f" left join file on image_file.file_id = file.id"
        return self._perform_select(query)

    def get_paged(self, page_size: int = 50, page_offset: int = 0):
        query = f"SELECT image_mipmap.id, path, extension, width, height, image_mip.id as mip_id, name, scale from image_mipmap" \
                f" left join image_mip on image_mip.map_id = image_mipmap.id" \
                f" left join image_file on image_mip.image_id = image_file.id" \
                f" left join file on image_file.file_id = file.id" \
                f" LIMIT {page_size} OFFSET {page_offset}"
        return self._perform_select(query)

    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        query = f"SELECT image_mipmap.id, path, extension, width, height, image_mip.id as mip_id, name, scale from image_mipmap" \
                f" left join image_mip on image_mip.map_id = image_mipmap.id" \
                f" left join image_file on image_mip.image_id = image_file.id" \
                f" left join file on image_file.file_id = file.id" \
                f" where image_mipmap.id in {allowed_ids}"
        return self._perform_select(query)


class TagClient(BaseClient):
    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        mapping = ("id", "name", "description", "class", "count")
        return tuple_to_dict(result, mapping)

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get_all(self):
        query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
                f" left join tag_map on tag.id = tag_map.tag_id group by tag.id"
        return self._perform_select(query)

    def get_paged(self, page_size: int = 50, page_offset: int = 0):
        query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
                f" left join tag_map on tag.id = tag_map.tag_id group by tag.id" \
                f" LIMIT {page_size} OFFSET {page_offset}"

        return self._perform_select(query)

    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_names = create_entry_string(kwargs.get('names', []))
        allowed_classes = create_entry_string(kwargs.get('classes', []))
        query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
                f" left join tag_map on tag.id = tag_map.tag_id" \
                f" where tag.id in {allowed_ids} or name in {allowed_names} or class in {allowed_classes}" \
                f" group by tag.id"
        return self._perform_select(query)


class PostClient(BaseClient):
    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        # post.id, post.name, post.description, tag_id, tag_name,tag_class, tag_count
        mapping = ("id", "name", "description", "tag_id", "tag_name", "tag_class", "tag_count", "tag_description")
        ungrouped = tuple_to_dict(result, mapping)
        grouped = {}
        for row in ungrouped:
            post_id = row['id']
            tag = {
                'id': row['tag_id'],
                'name': row['tag_name'],
                'description': row['tag_description'],
                'class': row['tag_class'],
                'count': row['tag_count'],
            }
            if post_id in grouped:
                grouped[post_id]['tags'].append(row)
            else:
                grouped[post_id] = {
                    'id': post_id,
                    'name': row['name'],
                    'description': row['description'],
                    'tags': [tag]
                }
        formatted = []
        for _, v in grouped.items():
            formatted.append(v)
        return formatted

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get_all(self):
        query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name, " \
                f"tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
                f" left join tag_map on post.id = tag_map.post_id" \
                f" left join tag on tag.id = tag_map.tag_id"
        return self._perform_select(query)

    def get_paged(self, page_size: int = 50, page_offset: int = 0):
        query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
                f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
                f" left join tag_map on post.id = tag_map.post_id" \
                f" left join tag on tag.id = tag_map.tag_id" \
                f" LIMIT {page_size} OFFSET {page_offset}"

        return self._perform_select(query)

    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_names = create_entry_string(kwargs.get('names', []))
        query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
                f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
                f" left join tag_map on post.id = tag_map.post_id" \
                f" left join tag on tag.id = tag_map.tag_id" \
                f" where post.id in {allowed_ids} or post.name in {allowed_names}"
        return self._perform_select(query)


class ImagePostClient(BaseClient):
    def __format_result(self, result: Union[Tuple, List[Tuple]]):
        # post.id, post.name, post.description, tag_id, tag_name,tag_class, tag_count
        mapping = ("id", "name", "description", "tag_id", "tag_name", "tag_class", "tag_count", "tag_description")
        ungrouped = tuple_to_dict(result, mapping)
        grouped = {}
        for row in ungrouped:
            post_id = row['id']
            tag = {
                'id': row['tag_id'],
                'name': row['tag_name'],
                'description': row['tag_description'],
                'class': row['tag_class'],
                'count': row['tag_count'],
            }
            if post_id in grouped:
                grouped[post_id]['tags'].append(row)
            else:
                grouped[post_id] = {
                    'id': post_id,
                    'name': row['name'],
                    'description': row['description'],
                    'tags': [tag]
                }
        formatted = []
        for _, v in grouped.items():
            formatted.append(v)
        return formatted

    def _perform_select(self, select_query: str):
        result = super()._perform_select(select_query)
        return self.__format_result(result)

    def get_all(self):
        query = f"SELECT image_post.id, post.id as post_id, post.name, post.description, tag.id as tag_id, tag.name as tag_name, " \
                f"tag.class as tag_class, count(image_post.post_id) as tag_count, tag.description as tag_description from image_post" \
                f" left join post on post.id = image_post.post_id" \
                f" left join tag_map on post.id = tag_map.post_id" \
                f" left join tag on tag.id = tag_map.tag_id"
        return self._perform_select(query)

    def get_paged(self, page_size: int = 50, page_offset: int = 0):
        query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
                f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
                f" left join tag_map on post.id = tag_map.post_id" \
                f" left join tag on tag.id = tag_map.tag_id" \
                f" LIMIT {page_size} OFFSET {page_offset}"

        return self._perform_select(query)

    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_names = create_entry_string(kwargs.get('names', []))
        query = f"SELECT post.id, post.name, post.description, tag.id as tag_id, tag.name as tag_name," \
                f" tag.class as tag_class, count(post_id) as tag_count, tag.description as tag_description from post" \
                f" left join tag_map on post.id = tag_map.post_id" \
                f" left join tag on tag.id = tag_map.tag_id" \
                f" where post.id in {allowed_ids} or post.name in {allowed_names}"
        return self._perform_select(query)


# OLD
class ImageClient:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def insert_images(self, **kwargs) -> Union[bool, None]:
        images = kwargs.get('images', [])
        for i in range(len(images)):
            image = images[i]
            if isinstance(image, dict):
                width = image.get('width', -1)
                height = image.get('height', -1)
                extension = image.get('extension', -1)
                images[i] = (width, height, extension)
            elif isinstance(image, ImageModel):
                width = image.width
                height = image.height
                extension = image.extension
                images[i] = (width, height, extension)

        values = create_value_string(images)

        query = f"INSERT INTO images(img_width, img_height, img_ext) VALUES {values}"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                con.commit()
                return True
        except sqlite3.DatabaseError:
            return None

    @staticmethod
    def __parse_image_rows(rows) -> List[ImageModel]:
        def create_link(name, id, ext):
            return {
                'name': name,
                'path': f"http://localhost:8000/images/posts/{id}/{name}.{ext}"
            }

        def create_image(id, ext, w, h):
            args = {
                'id': id,
                'width': w,
                'height': h,
                'extension': ext,
                'files': [
                    create_link('hirez', id, ext),
                    create_link('lorez', id, ext),
                    create_link('midrez', id, ext),
                    create_link('thumb', id, ext)
                ]
            }
            return ImageModel(**args)

        results = []
        current_image = None
        for img_id, img_ext, img_w, img_h, tag_id, tag_name, tag_count in rows:
            if current_image is None:
                current_image = create_image(img_id, img_ext, img_w, img_h)
            # Our query ensures img_ids are consecutive
            # This isn't done by  the order-by, but the order of our operations
            # As the left join on img_tag_map groups img_id
            elif current_image.id != img_id:
                results.append(current_image)
                current_image = create_image(img_id, img_ext, img_w, img_h)
            if tag_id is not None:
                tag_args = {
                    'id': tag_id,
                    'name': tag_name,
                    'count': tag_count
                }
                current_image.tags.append(TagModel(**tag_args))

        if current_image is not None:
            results.append(current_image)

        return results

    # noinspection SqlResolve
    def __get_image_info(self, selection_query: str):
        query = f"SELECT img_id, img_ext, img_width, img_height, tag_id, tag_name from ({selection_query}) left join image_tag_map on map_img_id = img_id left join tags on map_tag_id = tag_id"
        nested_query = "SELECT map_tag_id, count(map_img_id) as tag_count from image_tag_map group by map_tag_id"
        query = f"SELECT img_id, img_ext, img_width, img_height, tag_id, tag_name, tag_count from ({query}) left join ({nested_query}) on map_tag_id = tag_id"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                rows = cursor.fetchall()
                return ImageClient.__parse_image_rows(rows)
        except sqlite3.DatabaseError:
            raise

    # noinspection SqlResolve
    def get_images(self, **kwargs) -> List[ImageModel]:
        # Never trust user input; sanatize args
        img_id_array = kwargs.get('image_ids', [])
        entries = create_entry_string(img_id_array)  # sanatizes for us
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images where img_id in {entries} ORDER BY img_id DESC"
        return self.__get_image_info(query)

    # noinspection SqlResolve
    def get_images_paged(self, **kwargs) -> List[ImageModel]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        page_number = int(kwargs.get('page', 0))
        page_size = int(kwargs.get('page_size', 50))
        count = page_size
        offset = page_number * page_size
        return self.get_images_range(start=offset, count=count)

    # noinspection SqlResolve
    def get_images_range(self, **kwargs) -> List[ImageModel]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        start = int(kwargs.get('start', 0))
        stop_raw = kwargs.get('stop', None)
        count_raw = kwargs.get('count', None)
        if stop_raw:
            count = int(stop_raw) - start
        else:
            count = int(count_raw)
        offset = start
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC LIMIT {count} OFFSET {offset}"
        return self.__get_image_info(query)

#
# #OLD
# class TagClient:
#     def __init__(self, db_path: str):
#         self.db_path = db_path
#
#     def insert_tags(self, **kwargs) -> Union[List[TagModel], None]:
#         tag_names = kwargs.get('tag_names', [])
#         values = create_value_string(tag_names)
#         query = f"INSERT INTO tags(tag_name) VALUES {values}"
#
#         try:
#             with Conwrapper(self.db_path) as (con, cursor):
#                 cursor.execute(query)
#                 con.commit()
#                 return self.get_tags(tag_names=tag_names)
#         except sqlite3.DatabaseError:
#             return None
#
#     @staticmethod
#     def __parse_tag_rows(rows) -> List[TagModel]:
#         results = []
#         for tag_id, tag_name, tag_count in rows:
#             if tag_count is None:
#                 tag_count = 0
#
#             tag_args = {
#                 'id': tag_id,
#                 'name': tag_name,
#                 'count': tag_count
#             }
#             results.append(TagModel(**tag_args))
#         return results
#
#     # noinspection SqlResolve
#     def __get_tag_info(self, select_query: str) -> Union[None, List[TagModel]]:
#         query = f"SELECT tag_id, tag_name, count(map_img_id) as tag_count FROM ({select_query}) left join image_tag_map on tag_id = map_tag_id group by tag_id"
#
#         try:
#             with Conwrapper(self.db_path) as (con, cursor):
#                 cursor.execute(query)
#                 rows = cursor.fetchall()
#             return TagClient.__parse_tag_rows(rows)
#         except sqlite3.DatabaseError:
#             raise
#
#     # noinspection SqlResolve
#     def get_tags(self, **kwargs) -> Union[None, List[ImageModel]]:
#         # Never trust user input; sanatize args
#         tag_id_array = kwargs.get('tag_ids', [])
#         tag_names_array = kwargs.get('tag_names', [])
#         id_entries = create_entry_string(tag_id_array)  # sanatizes for us
#         name_entries = create_entry_string(tag_names_array)  # sanatizes for us
#         query = f"SELECT tag_id, tag_name FROM tags where tag_id in {id_entries} or tag_name in {name_entries} ORDER BY tag_id DESC"
#         return self.__get_tag_info(query)
#
#     def get_tags_paged(self, **kwargs: Dict[str, object]) -> List[TagModel]:
#         # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
#         page_number = int(kwargs.get('page', 0))
#         page_size = int(kwargs.get('page_size', 50))
#         count = page_size
#         offset = page_number * page_size
#         query = f"SELECT tag_id, tag_name FROM tags ORDER BY tag_id DESC LIMIT {count} OFFSET {offset}"
#         return self.__get_tag_info(query)
