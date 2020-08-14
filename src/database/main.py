import mimetypes
from os.path import splitext
from typing import List

from src.database.clients import FilePageClient, FileClient, FileTagClient, TagClient, PageClient


def create_all_tables(**kwargs):
    TagClient(**kwargs).create()
    FileClient(**kwargs).create()
    PageClient(**kwargs).create()

    FileTagClient(**kwargs).create()
    FilePageClient(**kwargs).create()


def insert_files(db_path, paths: List[str]):
    file_client = FileClient(db_path=db_path)
    page_client = PageClient(db_path=db_path)
    file_page_client = FilePageClient(db_path=db_path)

    for path in paths:
        mime = mimetypes.guess_type(path)[0]
        value = (path, mime)
        file_client.insert([value])
        file_id = file_client.fetch(paths=[path])[0]['id']

        # Check for page existing
        file_pages = file_page_client.fetch(files=[file_id])
        if len(file_pages) == 0:
            page_name, _ = splitext(path)
            page_client.insert([(page_name, "")])
            # Since name isnt unique this will fail
            # TODO FIX IT
            page_id = page_client.fetch(names=[page_name])[0]['id']
            file_page_client.insert([(file_id, page_id)])
