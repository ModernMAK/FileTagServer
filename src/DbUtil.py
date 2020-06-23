import sqlite3
from os.path import splitext, join
import src.PathUtil as PathUtil
from typing import Tuple, List, Union

from PIL import Image

# hardcoded for now, consider moving to a settings dict
database_path = PathUtil.data_path('imgserver.db')


class Conwrapper():
    def __init__(self, db_path: str):
        self.con = sqlite3.connect(db_path)
        self.cursor = self.con.cursor()

    def __enter__(self):
        return self.con, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()
        return exc_type is None


def initialize_db() -> None:
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS images(img_id integer PRIMARY KEY AUTOINCREMENT, img_ext text, img_width integer, img_height integer )")
        cursor.execute("CREATE TABLE IF NOT EXISTS tags(tag_id integer PRIMARY KEY AUTOINCREMENT, tag_name text)")
        con.commit()


def sanitize(data: Union[str, List, Tuple]) -> Union[str, List, Tuple]:
    def sanatize_single(single_data: str) -> str:
        sanatized = single_data.replace("'", "''")
        return sanatized

    if isinstance(data, (list, tuple)):
        for i in range(len(data)):
            data[i] = sanatize_single(data[i])
        return data
    else:
        return sanatize_single(data)


def create_entry_string(data: Union[object, List[object]]) -> List[str]:
    if isinstance(data, (List, Tuple)):
        for i in range(len(data)):
            data[i] = sanitize(str(data[i]))
        return [f"({','.join(data)})"]
    else:
        return [f"({sanitize(str(data))})"]


def create_value_string(values: Union[object, List[object], List[List[object]]]) -> str:
    if isinstance(values, (List, Tuple)):
        values = values.copy()
        for i in range(len(values)):
            values[i] = create_entry_string(values[i])
    else:
        values = create_entry_string(values)
    return ','.join(values)


def convert_tuple_to_list(values: List[Tuple[object]]) -> List[object]:
    result = []
    for (value,) in values:
        result.append(value)
    return result


def add_img(img_path: str, img: Image, root_path: str) -> int:
    from src import ImageUtil
    _, img_ext = splitext(img_path)
    stripped_img_ext = img_ext.strip('.')
    stripped_img_ext = sanitize(stripped_img_ext)
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(
            f"INSERT INTO images(img_width, img_height, img_ext) VALUES({img.width},{img.height}, '{stripped_img_ext}')")
        img_id = cursor.lastrowid
        img_save_path = join(root_path, str(img_id) + img_ext)
        ImageUtil.convert_to_imageset(img, img_save_path)
        con.commit()
        return img_id


def add_missing_tags(tag_list: List[str]):
    with Conwrapper(database_path) as (con, cursor):
        values = create_value_string(tag_list)
        # Should be one execute, but this is easier to code
        # tag_name is a unique column, and should err if we insert an illegal value
        cursor.execute(f"INSERT OR IGNORE INTO tags(tag_name) VALUES {values}")
        con.commit()


def set_img_tags(img_id: int, tag_list: List[str]) -> None:
    with Conwrapper(database_path) as (con, cursor):
        values = create_value_string(tag_list)

        # Get tag_ids to set
        cursor.execute(f"SELECT tag_id FROM tags WHERE tag_name IN ({values})")
        rows = cursor.fetchall()
        tag_id_list = create_entry_string(convert_tuple_to_list(rows))
        cursor.execute(f"DELETE FROM image_tag_map where map_img_id = {img_id} and map_tag_id NOT IN {tag_id_list}")

        pairs = []
        for tag_id in tag_id_list:
            pairs.append(({img_id}, {tag_id}))
        values = create_value_string(pairs)
        cursor.execute(f"INSERT OR IGNORE INTO image_tag_map (map_img_id, map_tag_id) VALUES {values}")

        con.commit()


def get_img(img_id: int) -> Tuple[str, int, int]:
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(f"SELECT img_ext, img_width, img_height FROM images WHERE img_id = {img_id}")
        row = cursor.fetchone()
        con.close()
    return row


def get_img_tags(img_id: int) -> List[Tuple[int, str]]:
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(
            f"SELECT tag_id, tag_name FROM image_tag_map, tags WHERE map_img_id = {img_id} and map_tag_id = tag_id")
        rows = cursor.fetchall()
        con.close()
    return rows


def get_imgs(count: int, offset: int = 0) -> List[Tuple[int, str, int, int]]:
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(
            f"SELECT img_id, img_ext, img_width, img_height FROM images ORDER BY img_id DESC LIMIT {count} OFFSET {offset}")
        rows = cursor.fetchall()
        con.close()
    return rows
