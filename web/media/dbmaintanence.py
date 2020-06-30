import src.DbUtil as dbutil
import src.PathUtil as pathutil
import os
from PIL import Image

db_path = pathutil.data_path('mediaserver.db')


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
            values.append(get_file_info(full_file))
    value_str = dbutil.create_value_string(values)
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"INSERT INTO file (real_path, extension) VALUES {value_str}"
        cursor.execute(query)
        conn.commit()


def fix_missing_image_files():
    image_ext_whitelist = ['bmp', 'png', 'apng', 'jpg', 'jpeg', 'ico', 'webp', 'gif', 'tif', 'tiff', 'bmp']

    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT id, real_path, extension from file"
        cursor.execute(query)
        rows = cursor.fetchall()
        images_found = []
        for (id, path, ext) in rows:
            if ext.lower() in image_ext_whitelist:
                try:
                    with Image.open(path) as img:
                        (w, h) = img.size
                        images_found.append((id, w, h))
                except NotImplementedError:
                    pass

        values = dbutil.create_value_string(images_found)
        query = f"Insert into image_file (file_id, width, height) VALUES {values}"
        cursor.execute(query)
        conn.commit()


def fix_file_ext_in_db():
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        query = f"SELECT id, real_path from file"
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


# Do not use later, this only works cause its hardcoded
def rebuild_mipmaps_and_image_post():
    with dbutil.Conwrapper(db_path) as (conn, cursor):
        for i in range(1, 17):
            query = f"INSERT into image_mipmap (id) VALUES ({i})"
            cursor.execute(query)

            query = f"INSERT into image_mip (image_id, map_id, name, scale) VALUES" \
                    f" ({(i - 1) * 4 + 0 + 1}, {i}, 'hirez', 1.0)," \
                    f" ({(i - 1) * 4 + 1 + 1}, {i}, 'lorez', 0.25)," \
                    f" ({(i - 1) * 4 + 2 + 1}, {i}, 'midrez', 0.5)," \
                    f" ({(i - 1) * 4 + 3 + 1}, {i}, 'thumb', NULL)"

            cursor.execute(query)

            query = f"INSERT into post (name, description) VALUES (NULL, NULL)"
            cursor.execute(query)
            post_id = cursor.lastrowid

            query = f"INSERT into image_post (id,post_id,mipmap_id) VALUES ({i},{post_id},{i})"
            cursor.execute(query)
            conn.commit()




if __name__ == '__main__':
    add_all_files(pathutil.image_path('posts'))
    fix_file_ext_in_db()
    fix_missing_image_files()
    rebuild_mipmaps_and_image_post()
