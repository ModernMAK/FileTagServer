import json
import mimetypes
import os
import sqlite3
from os.path import join, basename
from typing import Dict, List, Tuple, Iterable
from FileTagServer.DBI.file import CreateFileQuery, create_file


def load_settings(path: str = None) -> Dict:
    path = path or "settings.json"
    with open(path, "r") as settings:
        return json.load(settings)


def explore_paths(paths: List[str]) -> Iterable[Tuple[str, List[str], List[str]]]:
    for path in paths:
        for root, folders, files in os.walk(path):
            yield root, folders, files


def add_and_update_files(paths:List[str]):
    # TODO check if file name exists
    #   Check that Mimetype matches
    #       Generate a hash for the local file
    #           Compare against remote hashes
    #               For matches; check that file still exists
    #                   File does not exist; replace record's path to new path and do not insert
    # TODO After inserting, scan DB for files which no longer exist. and then delete those entires
    # Currently, only adds all paths
    for root, folders, files in explore_paths(paths):
        for file in files:
            path = join(root, file)
            mime = mimetypes.guess_type(path)[0]
            q = CreateFileQuery(path=path, mime=mime, name=basename(path))
            try:
                create_file(q)
            except sqlite3.IntegrityError:
                pass


if __name__ == "__main__":
    settings = load_settings()
    paths = settings.get('paths', [])
    add_and_update_files(paths)
