import hashlib
import json
import mimetypes
import os
import re
from typing import List

from src.database_api.clients import MasterClient
from src.database_api.clients.file_extra_info import FileExtraInfoTable
from src.page_groups import pathing


def scan_and_add(db_dir: str, root_dir: str, patterns: List = None, exts: List[str] = None):
    if patterns is None:
        patterns = []
    if exts is None:
        exts = []

    def check_ext(path: str) -> bool:
        my_e = os.path.splitext(path)[1].lstrip('.').lower()
        # print(my_e, *exts)
        if my_e in exts:
            return True
        return False

    def check_pattern(path: str) -> bool:
        for p in patterns:
            if p.match(path):
                return True
        return False

    mc = MasterClient(db_path=db_dir)

    def exists_in_db(path: str):
        result = mc.file.fetch(paths=[path])
        if result is None or len(result) == 0:
            return False
        return True

    def insert_into_db(path: str):
        # Path mime name desc
        mime = mimetypes.guess_type(path)[0]
        if mime is None:
            mime = ""
        name = os.path.basename(path)
        desc = ""  # for now no desc
        value = (path, mime, name, desc)
        mc.file.insert([value])

    def update_into_db(path: str):
        current = mc.file.fetch(paths=[path])[0]
        mime = mimetypes.guess_type(path)[0]
        if mime is None:
            mime = ""
        mc.file._execute(f"UPDATE file SET mime = '{mime}' where id = '{current['id']}'")

    def update_extra_info(path:str):
        current = mc.file.fetch(paths=[path])[0]
        id = current['id']
        size = os.stat(path).st_size

        def gen_hash(p:str):
            md5 = hashlib.md5()
            with open(p,"rb") as f:
                md5.update(f.read())
            return md5.hexdigest()


        hash = gen_hash(path)
        value = (id, hash, size)
        mc.file_info.insert([value])

        # mc.file._execute(f"INSERT OR REPLACE INTO {FileExtraInfoTable.table} SET mime = '{mime}' where id = '{current['id']}'")


    print(f"[Walking]\t{root_dir}\t=====================")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            full_file_path = os.path.join(root, file)
            if check_ext(full_file_path) or check_pattern(full_file_path):
                if not exists_in_db(full_file_path):
                    insert_into_db(full_file_path)
                    update_extra_info(full_file_path)
                    print(f"[Inserted]\t{full_file_path}")
                else:
                    update_into_db(full_file_path)
                    update_extra_info(full_file_path)
                    print(f"[Updating]\t{full_file_path}")
            else:
                print(f"[Not Allowed]\t{full_file_path}")


if __name__ == "__main__":
    mimetypes.add_type("video/webm", "webm")
    mimetypes.add_type("image/webp", "webp")

    db = pathing.Static.get_database(r"local.db")

    with open("scan_settings.json") as f:
        settings = json.load(f)

    paths = settings['paths']
    patterns_base = settings['patterns']
    exts = settings['exts']
    patterns = []
    for pattern in patterns_base:
        compiled = re.compile(pattern)
        patterns.append(compiled)

    exts = [e.lower() for e in exts]

    print(f"DB : {db}")
    input("Press Any Key to Continue...")
    mc = MasterClient(db_path=db)
    mc.create_all()

    for path in paths:
        scan_and_add(db, path, patterns, exts)
