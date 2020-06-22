import sqlite3
from os.path import splitext, join

# hardcoded for now, consider moving to a settings dict
from typing import Tuple, List

from PIL import Image

database_path = 'imgserver.db'


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


def add_img(img_path: str, img: Image, root_path: str) -> int:
    import ImageUtil
    _, img_ext = splitext(img_path)
    stripped_img_ext = img_ext.strip('.')
    stripped_img_ext = stripped_img_ext.replace("'", "''")
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
        formatted_tag = []
        for tag in tag_list:
            escaped_tag = tag.replace("'", "''")
            formatted_tag.append(f"('{escaped_tag}')")
        # Should be one execute, but this is easier to code
        # tag_name is a unique column, and should err if we insert an illegal value
        cursor.execute(f"INSERT OR IGNORE INTO tags(tag_name) VALUES {','.join(formatted_tag)}")
        con.commit()


def set_img_tags(img_id: int, tag_list: List[str]) -> None:
    with Conwrapper(database_path) as (con, cursor):
        formatted_tag_list = []
        for tag in tag_list:
            escaped_tag = tag.replace("'", "''")
            formatted_tag_list.append(f"'{escaped_tag}'")

        # Get tag_ids to set
        cursor.execute(f"SELECT tag_id FROM tags WHERE tag_name IN ({','.join(formatted_tag_list)})")
        rows = cursor.fetchall()
        tag_id_list = []
        for (row,) in rows:
            tag_id_list.append(str(row))

        cursor.execute(
            f"DELETE FROM image_tag_map where map_img_id = {img_id} and map_tag_id NOT IN ({','.join(tag_id_list)})")

        pairs = []
        for tag_id in tag_id_list:
            pairs.append(f"({img_id},{tag_id})")

        cursor.execute(f"INSERT OR IGNORE INTO image_tag_map (map_img_id, map_tag_id) VALUES {','.join(pairs)}")

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
