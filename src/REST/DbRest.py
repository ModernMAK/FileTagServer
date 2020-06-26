import sqlite3

from src import PathUtil
from src.DbUtil import sanitize, create_entry_string
from typing import Dict, Union, List

# hardcoded for now, consider moving to a settings dict
database_path = PathUtil.data_path('imgserver.db')


class Conwrapper:
    def __init__(self, db_path: str):
        self.con = sqlite3.connect(db_path)
        self.cursor = self.con.cursor()

    def __enter__(self):
        return self.con, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()
        return exc_type is None


class RestData:
    def to_dictionary(self):
        pass

    def from_dictionary(self, **kwargs):
        pass


class RestImage(RestData):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', -1)
        self.width = kwargs.get('width', 2)
        self.height = kwargs.get('height', 2)
        self.extension = kwargs.get('extension', '')
        self.tags = kwargs.get('tags', [])

    def from_dictionary(self, **kwargs):
        self.__init__(kwargs=kwargs)

    def to_dictionary(self):
        return {
            'id': self.id,
            'width': self.width,
            'height': self.height,
            'extension': self.extension,
        }


class RestTag(RestData):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', -1)
        self.name = kwargs.get('name', 2)

    def from_dictionary(self, **kwargs):
        self.__init__(kwargs=kwargs)

    def to_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class RestClient:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.image_client = ImageClient(db_path)


class ImageClient:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def insert_image(self, **kwargs) -> Union[RestImage, None]:
        width = kwargs.get('width', 2)
        height = kwargs.get('height', 2)
        extension = kwargs.get('extension', '')
        values = [width, height, extension]
        entry = create_entry_string(values)  # create_entry sanitizes for us

        query = f"INSERT INTO images(img_width, img_height, img_ext) VALUES {entry}"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                id = cursor.lastrowid
                con.commit()
                values = sanitize(values)
                result = {
                    'id': id,
                    'width': values[0],
                    'height': values[1],
                    'extension': values[2]
                }
                return RestImage(kwargs=result)
        except sqlite3.DatabaseError:
            return None

    def __parse_image_rows(self, rows) -> List[RestImage]:
        results = []
        current_image = None
        for img_id, img_ext, img_w, img_h, tag_id, tag_name in rows:

            if current_image is None:
                img_args = {
                    'id': img_id,
                    'width': img_w,
                    'height': img_h,
                    'extension': img_ext
                }
                current_image = RestImage(**img_args)
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
                current_image = RestImage(**img_args)

            if tag_id is not None:
                tag_args = {
                    'id': tag_id,
                    'name': tag_name
                }
                current_image.tags.append(RestTag(**tag_args))

        return results

    # noinspection SqlResolve
    def __get_image_info(self, selection_query: str):
        query = f"SELECT img_id, img_ext, img_width, img_height, map_tag_id from ({selection_query}) left join image_tag_map on map_img_id = img_id"
        query = f"SELECT img_id, img_ext, img_width, img_height, tag_id, tag_name from ({query}) left join tags on map_tag_id = tag_id"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                rows = cursor.fetchall()
                results = []
                current_image = None
                for img_id, img_ext, img_w, img_h, tag_id, tag_name in rows:

                    if current_image is None:
                        img_args = {
                            'id': img_id,
                            'width': img_w,
                            'height': img_h,
                            'extension': img_ext
                        }
                        current_image = RestImage(**img_args)
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
                        current_image = RestImage(**img_args)

                    if tag_id is not None:
                        tag_args = {
                            'id': tag_id,
                            'name': tag_name
                        }
                        current_image.tags.append(RestTag(**tag_args))

                return results
        except sqlite3.DatabaseError:
            return None

    # noinspection SqlResolve
    def get_images(self, **kwargs) -> List[RestImage]:
        # Never trust user input; sanatize args
        img_id_array = kwargs.get('image_ids', [])
        entries = create_entry_string(img_id_array)  # sanatizes for us
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC LIMIT where img_id in {entries}"
        return self.__get_image_info(query)

    # noinspection SqlResolve
    def get_images_paged(self, **kwargs: Dict[str, object]) -> List[RestImage]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        page_number = int(kwargs.get('page', 0))
        page_size = int(kwargs.get('page_size', 50))
        count = page_size
        offset = page_number * page_size
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC LIMIT {count} OFFSET {offset}"

        return self.__get_image_info(query)


class TagClient:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def insert_image(self, **kwargs) -> Union[RestImage, None]:
        width = kwargs.get('width', 2)
        height = kwargs.get('height', 2)
        extension = kwargs.get('extension', '')
        values = [width, height, extension]
        entry = create_entry_string(values)  # create_entry sanitizes for us

        query = f"INSERT INTO images(img_width, img_height, img_ext) VALUES {entry}"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                id = cursor.lastrowid
                con.commit()
                values = sanitize(values)
                result = {
                    'id': id,
                    'width': values[0],
                    'height': values[1],
                    'extension': values[2]
                }
                return RestImage(kwargs=result)
        except sqlite3.DatabaseError:
            return None

    def __parse_image_rows(self, rows) -> List[RestImage]:
        results = []
        current_image = None
        for img_id, img_ext, img_w, img_h, tag_id, tag_name in rows:

            if current_image is None:
                img_args = {
                    'id': img_id,
                    'width': img_w,
                    'height': img_h,
                    'extension': img_ext
                }
                current_image = RestImage(**img_args)
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
                current_image = RestImage(**img_args)

            if tag_id is not None:
                tag_args = {
                    'id': tag_id,
                    'name': tag_name
                }
                current_image.tags.append(RestTag(**tag_args))

        return results

    # noinspection SqlResolve
    def __get_image_info(self, selection_query: str):
        query = f"SELECT img_id, img_ext, img_width, img_height, map_tag_id from ({selection_query}) left join image_tag_map on map_img_id = img_id"
        query = f"SELECT img_id, img_ext, img_width, img_height, tag_id, tag_name from ({query}) left join tags on map_tag_id = tag_id"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                rows = cursor.fetchall()
                results = []
                current_image = None
                for img_id, img_ext, img_w, img_h, tag_id, tag_name in rows:

                    if current_image is None:
                        img_args = {
                            'id': img_id,
                            'width': img_w,
                            'height': img_h,
                            'extension': img_ext
                        }
                        current_image = RestImage(**img_args)
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
                        current_image = RestImage(**img_args)

                    if tag_id is not None:
                        tag_args = {
                            'id': tag_id,
                            'name': tag_name
                        }
                        current_image.tags.append(RestTag(**tag_args))

                return results
        except sqlite3.DatabaseError:
            return None

    # noinspection SqlResolve
    def get_images(self, **kwargs) -> List[RestImage]:
        # Never trust user input; sanatize args
        img_id_array = kwargs.get('image_ids', [])
        entries = create_entry_string(img_id_array)  # sanatizes for us
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC LIMIT where img_id in {entries}"
        return self.__get_image_info(query)

    # noinspection SqlResolve
    def get_images_paged(self, **kwargs: Dict[str, object]) -> List[RestImage]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        page_number = int(kwargs.get('page', 0))
        page_size = int(kwargs.get('page_size', 50))
        count = page_size
        offset = page_number * page_size
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC LIMIT {count} OFFSET {offset}"

        return self.__get_image_info(query)
