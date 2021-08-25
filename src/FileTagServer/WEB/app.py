from os.path import dirname
from typing import List, Dict

from fastapi import FastAPI
from starlette.responses import HTMLResponse

from FileTagServer.DBI.common import Util
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.file.file import get_orphaned_files, get_files
from FileTagServer.DBI.folder.folder import get_folder, get_folders, get_folder_by_path
from FileTagServer.DBI.folder.old_folder import get_root_folders
from FileTagServer.DBI.models import Folder, File, Tag
from FileTagServer.DBI.tag.tag import get_tags
from FileTagServer.REST.routing import reformat, file_route, tag_route
from FileTagServer.WEB.common import render
from FileTagServer.WEB.routing import root_route, orphaned_files_route, folder_route


def build_ancestry(name: str = "", url: str = "", path: str = "", add_self: bool = True):
    ancestry: List[Dict] = []
    if add_self:
        ancestry.append({'page': url, 'name': name})
    while True:
        path = dirname(path)
        try:
            parent_folder = get_folder_by_path(path)
            d = {
                'page': reformat(folder_route, folder_id=parent_folder.id),
                'name': parent_folder.name
            }
            ancestry.append(d)
        except ApiError:
            break
    ancestry.append({'page': root_route, 'name': '~'})
    ancestry = ancestry[::-1]  # reverse order
    ancestry[-1]['last'] = True
    return ancestry


def build_context(name: str, description: str, ancestry: List[Dict], folders: List[Folder], files: List[File],
                  tags: List[Tag]):
    folders = Util.dict(folders)
    for f in folders:
        f['page'] = reformat(folder_route, folder_id=f['id'])

    files = Util.dict(files)
    for f in files:
        f['page'] = reformat(file_route, file_id=f['id'])

    tags = Util.dict(tags)
    for t in tags:
        t['page'] = reformat(tag_route, tag_id=t['id'])

    return {
        'ancestry': ancestry,
        'name': name,
        'desc': description,
        'files': files,
        'folders': folders,
        'tags': tags
    }


def add_routes(app: FastAPI):
    @app.get(root_route)
    def root_folder():
        folders: List[Folder] = get_root_folders()
        ancestry = build_ancestry(add_self=False)  # Builds root only
        files = []  # get_orphaned_files()
        tags = []
        context = build_context("Root", None, ancestry, folders, files, tags)
        orphaned_folder = {
            'name': 'Orphaned Files',
            'id': '-',
            'page': orphaned_files_route
        }
        context['folders'].append(orphaned_folder)
        html = render("../static/html/folder/table.html", **context)
        return HTMLResponse(html)

    @app.get(folder_route)
    def sub_folder(folder_id: int):
        folder = get_folder(folder_id)
        folders: List[Folder] = get_folders(folder.folders)
        files = get_files(folder.files)
        tags = get_tags(folder.tags)
        ancestry = build_ancestry(folder.name, reformat(folder_route, folder_id=folder_id), folder.path)
        context = build_context(folder.name, folder.description, ancestry, folders, files, tags)
        html = render("../static/html/folder/table.html", **context)
        return HTMLResponse(html)

    @app.get(orphaned_files_route)
    def orphaned_file_folder():
        folders = []
        files = get_orphaned_files()
        tags = []
        ancestry = build_ancestry("Orphaned Files", orphaned_files_route)
        context = build_context(sub_folder.name, sub_folder.description, ancestry, folders, files, tags)
        html = render("../static/html/folder/table.html", **context)
        return HTMLResponse(html)
