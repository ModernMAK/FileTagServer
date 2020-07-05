import configparser

from src.util import path_util, db_util, dict_util, collection_util
import os
from src.content import content_gen
from src.API import models
from src.util import path_util
from src.util.dict_util import DictFormat
from src.Routing.virtual_access_points import RequiredVap

db_path = RequiredVap.data_real('mediaserver2.db')


def get_file_info(path: str):
    _, ext = os.path.splitext(path)
    ext = ext.lstrip('.')
    return path, ext


def add_all_files(path: str):
    values = []
    for root, directories, files in os.walk(path):
        for file in files:
            full_file = os.path.join(root, file)
            path, ext = get_file_info(full_file)
            if ext.lower() != 'meta':
                values.append((path, ext))
    value_str = db_util.create_value_string(values)
    with db_util.Conwrapper(db_path) as (conn, cursor):
        query = f"INSERT OR IGNORE INTO file (path, extension) VALUES {value_str}"
        cursor.execute(query)
        conn.commit()


def gen_missing_meta_files():
    with db_util.Conwrapper(db_path) as (conn, cursor):
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
    with db_util.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT file.id, file_page.id from file" \
                f" left join file_page on file.id = file_page.file_id"
        cursor.execute(query)
        rows = cursor.fetchall()
        mapping = ('file_id', 'file_page_id')
        formatted = collection_util.tuple_to_dict(rows, mapping)
        for row in formatted:
            if row['file_page_id'] is None:
                query = f"INSERT INTO page DEFAULT VALUES"
                cursor.execute(query)
                page_id = cursor.lastrowid
                query = f"INSERT INTO file_page (page_id, file_id) VALUES ({page_id}, {row['file_id']})"
                cursor.execute(query)
        conn.commit()


# noinspection SqlResolve
def fix_file_ext_in_db():
    with db_util.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT id, path from file"
        cursor.execute(query)
        rows = cursor.fetchall()
        fixed = []
        for (id, path) in rows:
            _, ext = get_file_info(path)
            fixed.append((id, ext))

        query = f"CREATE TEMP TABLE tmp_file_fixed (id integer, extension tinytext)"
        cursor.execute(query)

        values = db_util.create_value_string(fixed)
        query = f"INSERT INTO tmp_file_fixed (id, extension) VALUES {values}"
        cursor.execute(query)

        query = f"UPDATE file SET extension = (SELECT tmp_file_fixed.extension from tmp_file_fixed where tmp_file_fixed.id = file.id)"
        cursor.execute(query)

        query = f"DROP TABLE tmp_file_fixed"
        cursor.execute(query)

        conn.commit()


def rebuild_missing_file_generated_content(rebuild: bool = False, supress_error_ignore: bool = False):
    with db_util.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT id, path, extension from file"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            id, path, extension = row
            meta_path = path + '.meta'
            meta_d = dict_util.read_dict(meta_path, DictFormat.ini, default={})
            meta = models.FileMeta(**meta_d)

            gen_folder = RequiredVap.dynamic_generated_real(os.path.join('file', str(id)))
            if not supress_error_ignore and meta.error_ignore:
                print(f"Skipping: {id}\t{path}\n\tPreviously Generated an Error")
                continue

            print(f"Generating: {id}\t{path}")
            try:
                success = content_gen.ContentGeneration.generate(path, gen_folder, rebuild=rebuild)
                if success:
                    print(f"\tGenerated")
                    meta.error_ignore = False
                else:
                    print(f"\tNot Supported")
            except Exception as e:
                print(e)
                print(f"\tEncountered an Error!")
                meta.error_ignore = True
