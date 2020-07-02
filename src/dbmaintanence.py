import configparser
from os.path import splitext

import src.DbUtil as dbutil
import src.PathUtil as pathutil
import os

from src import PathUtil
from src.API.ModelClients import tuple_to_dict
import PIL
from src.ImageUtil import convert_to_imageset, enforce_dirs_exists

db_path = pathutil.data_real_path('mediaserver2.db')


def get_file_info(path: str):
    _, ext = os.path.splitext(path)
    ext = ext.lstrip('.')
    return (path, ext)


def add_all_files(path: str):
    # path = pathutil.image_path('posts')
    # print(path)
    values = []
    for root, directories, files in os.walk(path):
        for file in files:
            full_file = os.path.join(root, file)
            path, ext = get_file_info(full_file)
            if ext.lower() != 'meta':
                values.append((path, ext))
    value_str = dbutil.create_value_string(values)
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"INSERT OR IGNORE INTO file (path, extension) VALUES {value_str}"
        cursor.execute(query)
        conn.commit()


def gen_missing_meta_files():
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT id, path from file"
        cursor.execute(query)
        rows = cursor.fetchall()
        for id, path in rows:
            meta_path = path + ".meta"
            parser = configparser.ConfigParser()
            if not os.path.exists(meta_path):
                with open(meta_path, 'w') as meta_f:
                    if 'File' not in parser.sections():
                        parser.add_section('File')
                    parser.set('File', 'id', str(id))
                    parser.write(meta_f)


def fix_missing_pages():
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT file.id, file_page.id from file" \
                f" left join file_page on file.id = file_page.file_id"
        cursor.execute(query)
        rows = cursor.fetchall()
        mapping = ('file_id', 'file_page_id')
        formatted = tuple_to_dict(rows, mapping)
        for row in formatted:
            if row['file_page_id'] is None:
                query = f"INSERT INTO page DEFAULT VALUES"
                cursor.execute(query)
                page_id = cursor.lastrowid
                query = f"INSERT INTO file_page (page_id, file_id) VALUES ({page_id}, {row['file_id']})"
                cursor.execute(query)
        conn.commit()


def fix_file_ext_in_db():
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT id, path from file"
        cursor.execute(query)
        rows = cursor.fetchall()
        fixed = []
        for (id, path) in rows:
            _, ext = get_file_info(path)
            fixed.append((id, ext))

        query = f"CREATE TEMP TABLE tmp_file_fixed (id integer, extension tinytext)"
        cursor.execute(query)

        values = dbutil.create_value_string(fixed)
        query = f"INSERT INTO tmp_file_fixed (id, extension) VALUES {values}"
        cursor.execute(query)

        query = f"UPDATE file SET extension = (SELECT tmp_file_fixed.extension from tmp_file_fixed where tmp_file_fixed.id = file.id)"
        cursor.execute(query)

        query = f"DROP TABLE tmp_file_fixed"
        cursor.execute(query)

        conn.commit()


def get_legal_image_ext():
    return ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']


def rebuild_missing_file_generated_content(dont_rebuilt: bool = False):
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        legal_images = get_legal_image_ext()
        query = f"SELECT id, path, extension from file"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            id, path, extension = row
            gen_folder = PathUtil.dynamic_generated_real_path(f'file/{id}')
            if os.path.exists(gen_folder) and dont_rebuilt:
                continue

            if extension.lower() in legal_images:
                enforce_dirs_exists(gen_folder)
                try:
                    real_path = path
                    _, ext = splitext(real_path)
                    with PIL.Image.open(real_path) as img:
                        convert_to_imageset(img, gen_folder, extension)
                except PIL.UnidentifiedImageError as e:
                    print(e)
                    pass
                except PIL.Image.DecompressionBombError as e:
                    print(e)
                    pass
                except OSError as e:
                    print(e)
                    pass
                except ValueError as e:
                    print(e)
                    pass


if __name__ == '__main__':
    add_all_files(pathutil.image_real_path('posts'))
    fix_file_ext_in_db()
    fix_missing_pages()
    rebuild_missing_file_generated_content()
