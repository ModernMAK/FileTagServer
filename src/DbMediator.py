import sqlite3
from os.path import splitext, join
import src.PathUtil as PathUtil
from typing import Tuple, List, Union
import src.API.Clients as DbRest
from src.DbUtil import Conwrapper, sanitize, create_value_string, create_entry_string, convert_tuple_to_list
from PIL import Image

# hardcoded for now, consider moving to a settings dict
database_path = PathUtil.data_path('imgserver.db')


def initialize_db() -> None:
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS images(img_id integer PRIMARY KEY AUTOINCREMENT, img_ext text, img_width integer, img_height integer )")
        cursor.execute("CREATE TABLE IF NOT EXISTS tags(tag_id integer PRIMARY KEY AUTOINCREMENT, tag_name text)")
        con.commit()


def add_img(img_path: str, img: Image, root_path: str) -> int:
    from src import ImageUtil
    _, img_ext = splitext(img_path)
    stripped_img_ext = img_ext.strip('.')
    stripped_img_ext = sanitize(stripped_img_ext)
    query = f"INSERT INTO images(img_width, img_height, img_ext) VALUES({img.width},{img.height}, {stripped_img_ext})"
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(query)
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
        tag_id_list = convert_tuple_to_list(rows)
        tag_id_collection = create_entry_string(tag_id_list)
        cursor.execute(
            f"DELETE FROM image_tag_map where map_img_id = {img_id} and map_tag_id NOT IN {tag_id_collection}")

        pairs = []
        for tag_id in tag_id_list:
            pairs.append((img_id, tag_id))
        values = create_value_string(pairs)
        cursor.execute(f"INSERT OR IGNORE INTO image_tag_map (map_img_id, map_tag_id) VALUES {values}")

        con.commit()


def get_img(img_id: int) -> Union[None, DbRest.ImageModel]:
    r_client = DbRest.ApiClient(database_path)
    return r_client.image_client.get_images(image_ids=[img_id])


def get_img_tags(img_id: int) -> List[DbRest.TagModel]:
    r_client = DbRest.ApiClient(database_path)
    return r_client.tag_client.get_tags(tag_ids=[img_id])


def get_imgs(count: int, offset: int = 0) -> List[DbRest.ImageModel]:
    r_client = DbRest.ApiClient(database_path)
    return r_client.image_client.get_images_paged(page=offset, page_size=count)


def get_imgs_tags_from_imgs(imgs: List[DbRest.ImageModel]) -> List[DbRest.TagModel]:
    unique_tags = set()
    for img in imgs:
        for tag in img.tags:
            unique_tags.add(tag)
    tag_list = list(unique_tags)

    def get_sort_key(element: DbRest.TagModel):
        return element.count

    tag_list.sort(reverse=True, key=get_sort_key)

    return tag_list


# Does not include untagged images -> Probably wont be supported, as it's a fringe case and has to be done intentially 'NOT A OR NOT B'
# noinspection SqlResolve
def search_imgs(search: str, count: int, offset: int = 0) -> List[Tuple[int, str, int, int]]:
    if not search:
        return get_imgs(count, offset)

    def parse_search(input: str):
        phrases = input.split()
        first_parse = []
        # first pass, fix tags and allow OR/NOT/AND
        for phrase in phrases:
            if phrase.upper() in ['OR', 'NOT', 'AND']:
                first_parse.append(('op', phrase.upper()))
                continue
            phrase = phrase.replace('_', ' ')
            phrase = sanitize(phrase)
            first_parse.append(('tag', phrase))

        second_parse = []
        second_parse_inv = []
        prev_tag = False
        prev_op = False
        negate_tag = False
        for code, content in first_parse:
            if code == 'op':
                if content == 'NOT':
                    negate_tag = not negate_tag
                else:
                    second_parse.append(content)
                    if content == 'AND':
                        second_parse_inv.append('OR')
                    else:
                        second_parse_inv.append('AND')
                    prev_op = True
                    prev_tag = False
            else:
                if not prev_op and prev_tag:  # prev_tag prevents this from running when we start with a tag
                    second_parse.append('AND')
                    second_parse_inv.append('OR')
                compare = "="
                inv_compare = "!="
                if negate_tag:
                    compare = "!="
                    inv_compare = "="
                    negate_tag = False
                second_parse.append(f'tag_name {compare} {content}')
                second_parse_inv.append(f'tag_name {inv_compare} {content}')
                prev_op = False
                prev_tag = True
        return ' '.join(second_parse), ' '.join(second_parse_inv)

    search_clause, search_clause_inv = parse_search(search)
    # Grabs a table with img_id, tag_id, and tag_name
    map_query = f"SELECT map_img_id, tag_id, tag_name from image_tag_map inner join tags on map_tag_id = tag_id"
    # Grabs only records which match the tags
    search_query = f"SELECT map_img_id FROM ({map_query}) where {search_clause}  group by map_img_id order by map_img_id"
    search_query_inv = f"SELECT map_img_id FROM ({map_query}) where {search_clause_inv} group by map_img_id order by map_img_id"
    img_query = f"SELECT img_id, img_ext, img_width, img_height FROM images where img_id in ({search_query}) and img_id not in ({search_query_inv}) ORDER BY img_id DESC LIMIT {count} OFFSET {offset}"
    with Conwrapper(database_path) as (con, cursor):
        cursor.execute(img_query)
        rows = cursor.fetchall()
        con.close()
    return rows


def get_tags(count: int, offset: int = 0) -> Union[List[DbRest.TagModel], None]:
    r_client = DbRest.ApiClient(database_path)
    return r_client.tag_client.get_tags_paged(page=offset, page_size=count)


def get_tag(tag_id: int) -> Union[DbRest.TagModel, None]:
    r_client = DbRest.ApiClient(database_path)
    return r_client.tag_client.get_tags(tag_ids=[tag_id])
