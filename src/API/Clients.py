import sqlite3

from typing import Dict, Union, List

from src.DbUtil import Conwrapper, create_entry_string, create_value_string
from src.API.Models import ImageModel, TagModel


class ApiClient:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.image_client = ImageClient(db_path)
        self.tag_client = TagClient(db_path)


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
        results = []
        current_image = None
        for img_id, img_ext, img_w, img_h, tag_id, tag_name, tag_count in rows:

            if current_image is None:
                img_args = {
                    'id': img_id,
                    'width': img_w,
                    'height': img_h,
                    'extension': img_ext
                }
                current_image = ImageModel(**img_args)
            # Our query ensures img_ids are consecutive
            # This isn't done by  the order-by, but the order of our operations
            # As the left join on img_tag_map groups img_id
            elif current_image.id != img_id:
                results.append(current_image)
                img_args = {
                    'id': img_id,
                    'width': img_w,
                    'height': img_h,
                    'extension': img_ext
                }
                current_image = ImageModel(**img_args)

            if tag_id is not None:
                tag_args = {
                    'id': tag_id,
                    'name': tag_name,
                    'count': tag_count
                }
                current_image.tags.append(TagModel(**tag_args))

        if current_image is not  None:
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


class TagClient:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def insert_tags(self, **kwargs) -> Union[List[TagModel], None]:
        tag_names = kwargs.get('tag_names', [])
        values = create_value_string(tag_names)
        query = f"INSERT INTO tags(tag_name) VALUES {values}"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                con.commit()
                return self.get_tags(tag_names=tag_names)
        except sqlite3.DatabaseError:
            return None

    @staticmethod
    def __parse_tag_rows(rows) -> List[TagModel]:
        results = []
        for tag_id, tag_name, tag_count in rows:
            if tag_count is None:
                tag_count = 0

            tag_args = {
                'id': tag_id,
                'name': tag_name,
                'count': tag_count
            }
            results.append(TagModel(**tag_args))
        return results

    # noinspection SqlResolve
    def __get_tag_info(self, select_query: str) -> Union[None, List[TagModel]]:
        query = f"SELECT tag_id, tag_name, count(map_img_id) as tag_count FROM ({select_query}) left join image_tag_map on tag_id = map_tag_id group by tag_id"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                rows = cursor.fetchall()
            return TagClient.__parse_tag_rows(rows)
        except sqlite3.DatabaseError:
            raise

    # noinspection SqlResolve
    def get_tags(self, **kwargs) -> Union[None, List[ImageModel]]:
        # Never trust user input; sanatize args
        tag_id_array = kwargs.get('tag_ids', [])
        tag_names_array = kwargs.get('tag_names', [])
        id_entries = create_entry_string(tag_id_array)  # sanatizes for us
        name_entries = create_entry_string(tag_names_array)  # sanatizes for us
        query = f"SELECT tag_id, tag_name FROM tags where tag_id in {id_entries} or tag_name in {name_entries} ORDER BY tag_id DESC"
        return self.__get_tag_info(query)

    def get_tags_paged(self, **kwargs: Dict[str, object]) -> List[TagModel]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        page_number = int(kwargs.get('page', 0))
        page_size = int(kwargs.get('page_size', 50))
        count = page_size
        offset = page_number * page_size
        query = f"SELECT tag_id, tag_name FROM tags ORDER BY tag_id DESC LIMIT {count} OFFSET {offset}"
        return self.__get_tag_info(query)
