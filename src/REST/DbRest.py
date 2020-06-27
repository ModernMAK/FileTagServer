import sqlite3

from typing import Dict, Union, List

from src.DbUtil import Conwrapper, create_entry_string, create_value_string


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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.id != other.id \
                    or self.width != other.width \
                    or self.height != other.height \
                    or self.extension != other.extension:
                return False
            # TODO compare tags,
            # Each tag should also be in other (and every tag in other should be in self)
            # We dont care about duplicates or tag order
            # Another way to describe this, we need to get a unique set from both
            # Then check that the unique sets are identical, ignoring order
            return True

    def __hash__(self):
        prime_a = 17
        prime_b = 23
        result = prime_a
        result = (result * prime_b) + self.id.__hash__()
        result = (result * prime_b) + self.width.__hash__()
        result = (result * prime_b) + self.height.__hash__()
        result = (result * prime_b) + self.extension.__hash__()
        # TODO perform hash on tags
        # since (as of this being written) __eq__ does not check tags, this is fine for now
        return result

    def __str__(self):

        return f"{self.id}: ({self.width} px, {self.height} px) ~ '.{self.extension}'"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

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
        self.count = kwargs.get('count', 0)

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'count': self.count
        }

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.id != other.id \
                    or self.id != other.id \
                    or self.name != other.name \
                    or self.count != other.count:
                return False
            return True

    def __str__(self):
        return f"{self.id}: {self.name} ~ {self.count}"

    def __hash__(self):
        prime_a = 23
        prime_b = 29
        result = prime_a
        result = (result * prime_b) + self.id.__hash__()
        result = (result * prime_b) + self.name.__hash__()
        result = (result * prime_b) + self.count.__hash__()
        return result


class RestClient:
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
            elif isinstance(image, RestImage):
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
    def __parse_image_rows(rows) -> List[RestImage]:
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
                    'name': tag_name,
                    'count': tag_count
                }
                current_image.tags.append(RestTag(**tag_args))

        return results

    # noinspection SqlResolve
    def __get_image_info(self, selection_query: str):
        query = f"SELECT img_id, img_ext, img_width, img_height, map_img_id, map_tag_id from ({selection_query}) left join image_tag_map on map_img_id = img_id"
        query = f"SELECT img_id, img_ext, img_width, img_height, tag_id, tag_name, count(map_img_id) as tag_count from ({query}) left join tags on map_tag_id = tag_id group by img_id"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                rows = cursor.fetchall()
                return ImageClient.__parse_image_rows(rows)
        except sqlite3.DatabaseError:
            return None

    # noinspection SqlResolve
    def get_images(self, **kwargs) -> List[RestImage]:
        # Never trust user input; sanatize args
        img_id_array = kwargs.get('image_ids', [])
        entries = create_entry_string(img_id_array)  # sanatizes for us
        query = f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC where img_id in {entries}"
        return self.__get_image_info(query)

    # noinspection SqlResolve
    def get_images_paged(self, **kwargs) -> List[RestImage]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        page_number = int(kwargs.get('page', 0))
        page_size = int(kwargs.get('page_size', 50))
        count = page_size
        offset = page_number * page_size
        return self.get_images_range(start=offset, count=count)

    # noinspection SqlResolve
    def get_images_range(self, **kwargs) -> List[RestImage]:
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

    def insert_tags(self, **kwargs) -> Union[List[RestTag], None]:
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
    def __parse_tag_rows(rows) -> List[RestTag]:
        results = []
        for tag_id, tag_name, tag_count in rows:
            if tag_count is None:
                tag_count = 0

            tag_args = {
                'id': tag_id,
                'name': tag_name,
                'count': tag_count
            }
            results.append(RestTag(**tag_args))
        return results

    # noinspection SqlResolve
    def __get_tag_info(self, select_query: str) -> Union[None, List[RestTag]]:
        query = f"SELECT tag_id, tag_name, count(map_img_id) as tag_count FROM ({select_query} left join image_tag_map on tag_id = map_tag_id group by tag_id"

        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(query)
                rows = cursor.fetchall()
            return TagClient.__parse_tag_rows(rows)
        except sqlite3.DatabaseError:
            return None

    # noinspection SqlResolve
    def get_tags(self, **kwargs) -> Union[None, List[RestImage]]:
        # Never trust user input; sanatize args
        tag_id_array = kwargs.get('tag_ids', [])
        tag_names_array = kwargs.get('tag_names', [])
        id_entries = create_entry_string(tag_id_array)  # sanatizes for us
        name_entries = create_entry_string(tag_names_array)  # sanatizes for us
        query = f"SELECT tag_id, tag_name FROM tags where tag_id in {id_entries} or tag_name in {name_entries} ORDER BY tag_id DESC"
        return self.__get_tag_info(query)

    def get_tags_paged(self, **kwargs: Dict[str, object]) -> List[RestTag]:
        # Never trust user input; i dont think we need to sanatize, since it should drop anything that cant be an int
        page_number = int(kwargs.get('page', 0))
        page_size = int(kwargs.get('page_size', 50))
        count = page_size
        offset = page_number * page_size
        query = f"SELECT tag_id, tag_name FROM tags ORDER BY tag_id DESC LIMIT {count} OFFSET {offset}"
        return self.__get_tag_info(query)
