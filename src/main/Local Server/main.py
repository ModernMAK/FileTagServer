import json
import mimetypes
import os
import sqlite3
from os.path import join
from typing import Dict, List

from FileTagServer.DBI.common import initialize_database
from FileTagServer.DBI.file.old_file import CreateFileQuery, create_file, FilePathQuery, get_file_by_path
from FileTagServer.DBI.folder.old_folder import create_folder, CreateFolderQuery, FolderPathQuery, \
    get_folder_by_path
from FileTagServer.DBI.folder_children import AddSubFolderQuery, AddSubFileQuery, add_folder_to_folder, \
    add_file_to_folder


def load_settings(path: str = None) -> Dict:
    path = path or "settings.json"
    with open(path, "r") as settings:
        return json.load(settings)


def add_and_update_files(db_path, paths: List[str]):
    # TODO check if file name exists
    #   Check that Mimetype matches
    #       Generate a hash for the local file
    #           Compare against remote hashes
    #               For matches; check that file still exists
    #                   File does not exist; replace record's path to new path and do not insert
    # TODO After inserting, scan DB for files which no longer exist. and then delete those entires
    # Currently, only adds all paths
    for path in paths:
        print(path)
        q = CreateFolderQuery(path=path, name=path)
        try:
            create_folder(db_path, q)
        except sqlite3.IntegrityError:
            pass

        for cur_dir, folders, files in os.walk(path):
            print("\t", cur_dir)
            q = FolderPathQuery(path=cur_dir)
            parent_f = get_folder_by_path(db_path, q)

            print("\t\t", "Folders")
            for folder in folders:
                print("\t\t\t", folder)
                folder_path = join(cur_dir, folder)
                try:
                    q = CreateFolderQuery(path=folder_path, name=folder)
                    f = create_folder(db_path, q)
                except sqlite3.IntegrityError:
                    q = FolderPathQuery(path=folder_path)
                    f = get_folder_by_path(db_path, q)

                try:
                    q = AddSubFolderQuery(parent_id=parent_f.id, child_id=f.id)
                    add_folder_to_folder(db_path, q)
                except sqlite3.IntegrityError:
                    continue

            print("\t\t", "Files")
            for file in files:
                print("\t\t\t", file)
                file_path = join(cur_dir, file)
                mime = mimetypes.guess_type(file_path)[0]
                try:
                    q = CreateFileQuery(path=file_path, mime=mime, name=file)
                    f = create_file(db_path, q)
                except sqlite3.IntegrityError:
                    q = FilePathQuery(path=file_path)
                    f = get_file_by_path(db_path, q)

                try:
                    q = AddSubFileQuery(folder_id=parent_f.id, file_id=f.id)
                    add_file_to_folder(db_path, q)
                except sqlite3.IntegrityError:
                    continue


if __name__ == "__main__":
    initialize_database()
    settings = load_settings()
    db_path = r"C:\Users\andre\Documents\GitHub\FileTagServer\local.db"
    initialize_database(db_path)
    paths = settings.get('paths', [])
    add_and_update_files(db_path, paths)
