import hashlib
import json
import mimetypes
import os
import sqlite3
from os.path import join, abspath
from typing import Dict, List

from FileTagServer.DBI.common import initialize_database
from FileTagServer.DBI.database import Database
from FileTagServer.DBI.file.file import CreateFileQuery, FilePathQuery
from FileTagServer.DBI.file.models import ModifyFileQuery
from FileTagServer.DBI.folder.folder import CreateFolderQuery, FolderPathQuery

from FileTagServer.DBI.folder_children import AddSubFolderQuery, AddSubFileQuery, FolderChildrenDBI
from FileTagServer.WEB.app import LocalPathConfig


def load_settings(path: str = None) -> Dict:
    path = path or "settings.json"
    with open(path, "r") as settings:
        return json.load(settings)


def gen_md5_hash(path: str, chunk_size: int = 1024 * 16):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def add_and_update_files(db_path, sql_path, paths: List[str]):
    # TODO check if file name exists
    #   Check that Mimetype matches
    #       Generate a hash for the local file
    #           Compare against remote hashes
    #               For matches; check that file still exists
    #                   File does not exist; replace record's path to new path and do not insert
    # TODO After inserting, scan DB for files which no longer exist. and then delete those entires
    # Currently, only adds all paths
    db = Database(db_path, sql_path)
    for path in paths:
        print(path)
        q = CreateFolderQuery(path=path, name=path)
        try:
            db.folder.query.create_folder(q)
        except sqlite3.IntegrityError:
            pass

        for cur_dir, folders, files in os.walk(path):
            print("\t", cur_dir)
            q = FolderPathQuery(path=cur_dir)
            parent_f = db.folder.query.get_folder_by_path(q)

            print("\t\t", "Folders")
            for folder in folders:
                print("\t\t\t", folder)
                folder_path = join(cur_dir, folder)
                try:
                    q = CreateFolderQuery(path=folder_path, name=folder)
                    f = db.folder.query.create_folder(q)
                except sqlite3.IntegrityError:
                    q = FolderPathQuery(path=folder_path)
                    f = db.folder.query.get_folder_by_path(q)

                try:
                    q = AddSubFolderQuery(parent_id=parent_f.id, child_id=f.id)
                    db.folder_children.add_folder_to_folder(q)
                except sqlite3.IntegrityError:
                    continue

            print("\t\t", "Files")
            for file in files:
                print("\t\t\t", file)
                file_path = join(cur_dir, file)
                mime = mimetypes.guess_type(file_path)[0]
                try:
                    q = CreateFileQuery(path=file_path, mime=mime, name=file)
                    f = db.file.query.create_file(q)
                except sqlite3.IntegrityError:
                    q = FilePathQuery(path=file_path)
                    f = db.file.query.get_file_by_path(q)

                try:
                    file_hash = gen_md5_hash(f.path)
                    stats = os.stat(f.path)
                    q = ModifyFileQuery(id=f.id, size_bytes=stats.st_size, date_created=stats.st_ctime, date_modified=stats.st_mtime, hash_md5=file_hash)
                    db.file.query.modify_file(q)
                except sqlite3.IntegrityError:
                    pass

                try:
                    q = AddSubFileQuery(folder_id=parent_f.id, file_id=f.id)
                    db.folder_children.add_file_to_folder(q)
                except sqlite3.IntegrityError:
                    continue


if __name__ == "__main__":
    # local >> main >> src >> FTS (project) << web
    local_pathing = LocalPathConfig("../../../web")
    settings = load_settings()
    db_path = abspath(join(__file__, r"../../local.db"))
    sql_path = str(local_pathing.sql)
    initialize_database(db_path, sql_path)
    paths = settings.get('paths', [])
    add_and_update_files(db_path, sql_path, paths)
