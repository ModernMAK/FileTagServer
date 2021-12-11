from os.path import dirname
from typing import List, Dict, Optional

from fastapi import FastAPI, Header
from pystache import Renderer
from starlette.responses import HTMLResponse

from FileTagServer.DBI.common import Util
from FileTagServer.DBI.database import Database
from FileTagServer.DBI.error import ApiError
# from FileTagServer.DBI.file.file import get_orphaned_files, get_files
# from FileTagServer.DBI.folder.folder import get_folder, get_folders, get_folder_by_path
from FileTagServer.DBI.folder.old_folder import get_root_folders
from FileTagServer.DBI.models import Folder, File, Tag
# from FileTagServer.DBI.tag.tag import get_tags
from FileTagServer.DBI.webconverter import WebConverter
from FileTagServer.REST.routing import reformat
from FileTagServer.WEB.common import serve_streamable
from FileTagServer.WEB.routing import root_route, orphaned_files_route, folder_route, file_route, tag_route, file_data_route


def get_icon(name: str) -> str:
    return f"bi-{name}"
    # return f"/img/bootstrap/{name}.svg"


def get_folder_icon():
    return get_icon("folder-fill")


def get_file_icon_name(mime: Optional[str] = None):
    unknown = "file-earmark-fill"
    if not mime:
        return unknown

    main, minor = mime.split("/")
    if main == "application":
        app_lookup = {
            "pdf": "file-earmark-pdf-fill"
        }
        return app_lookup.get(main, unknown)
    else:
        main_lookup = {
            "image": "file-earmark-image-fill",
            "audio": "file-earmark-music-fill",
            "video": "file-earmark-play-fill",
        }
        return main_lookup.get(main, unknown)


def get_file_icon(mime: Optional[str] = None) -> str:
    return get_icon(get_file_icon_name(mime))


def build_ancestry(database: Database, name: str = "", url: str = "", path: str = "", add_self: bool = True):
    ancestry: List[Dict] = []
    if add_self:
        ancestry.append({'page': url, 'name': name})
    while True:
        path = dirname(path)
        try:
            parent_folder = database.folder.get_folder_by_path(path)
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


def build_context(conv: WebConverter, name: str, description: str, ancestry: List[Dict], folders: List[Folder], files: List[File], tags: List[Tag], all_tags: List[Tag] = None):
    tag_lookup = {t.id: conv.tag(t) for t in all_tags} if all_tags else None

    folders = [conv.folder(f, tag_lookup) for f in folders] if folders else []
    files = [conv.file(f, tag_lookup) for f in files] if files else []
    # Use lookup to avoid reconverting, otherwise convert
    tags = ([conv.tag(t) for t in tags] if not tag_lookup else [tag_lookup[t.id] for t in tags]) if tags else []

    return {
        'ancestry': ancestry,
        'name': name,
        'desc': description,
        'files': Util.dict(files),
        'folders': Util.dict(folders),
        'tags': Util.dict(tags)
    }


def create_webconv() -> WebConverter:
    return WebConverter(
        folder_route,
        get_folder_icon,
        file_route,
        get_file_icon,
        tag_route
    )


def add_routes(app: FastAPI, renderer: Renderer, database: Database, webconv: WebConverter):

    def _folder(context: Dict, list_view: bool = True):
        template_name = "list" if list_view else "table"
        html = renderer.render_path(f"../static/html/folder/{template_name}.html", **context)
        return HTMLResponse(html)


    @app.get(root_route)
    def root_folder():
        folders: List[Folder] = get_root_folders(database.database_file)
        ancestry = build_ancestry(database, add_self=False)  # Builds root only
        files = None  # get_orphaned_files()
        tags = None
        context = build_context(webconv, "Root", None, ancestry, folders, files, tags)
        orphaned_folder = {
            'name': 'Orphaned Files',
            'id': '-',
            'icon': get_folder_icon(),
            'page': orphaned_files_route
        }
        context['folders'].append(orphaned_folder)
        return _folder(context)

    @app.get(folder_route)
    def sub_folder(folder_id: int):
        folder = database.folder.get_folder(folder_id)
        subfolders: List[Folder] = database.folder.get_folders(folder.folders)
        files = database.file.get_files(folder.files)

        all_tags = webconv.collect_nested_tags(folder, subfolders, files)
        tag_lookup = database.tag.get_tags(all_tags)
        tags = [tag_lookup[tag_id] for tag_id in folder.tags] if folder.tags else None

        ancestry = build_ancestry(database, folder.name, reformat(folder_route, folder_id=folder_id), folder.path)
        context = build_context(webconv, folder.name, folder.description, ancestry, subfolders, files, tags, tag_lookup)
        return _folder(context)

    @app.get(orphaned_files_route)
    def orphaned_file_folder():
        folder = None
        subfolders = None
        files = database.file.get_orphaned_files()

        all_tags = webconv.collect_nested_tags(folder, subfolders, files)
        tag_lookup = database.tag.get_tags(all_tags)
        tags = None

        ancestry = build_ancestry(database, "Orphaned Files", orphaned_files_route)
        context = build_context(webconv, "Orphaned Files", "Files with no parent folder.", ancestry, subfolders, files, tags, tag_lookup)
        return _folder(context)

    @app.get(file_route)
    def file(file_id: int, range: Optional[str] = Header(None)):
        file = database.file.get_file(file_id)
        return serve_streamable(file.path, range, file.name)