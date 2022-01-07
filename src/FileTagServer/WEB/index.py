import datetime
import json
from os.path import dirname, basename
from typing import List, Dict, Optional

from fastapi import Header
from starlette.responses import HTMLResponse, FileResponse

from FileTagServer.DBI.common import Util
from FileTagServer.DBI.database import Database
from FileTagServer.DBI.error import ApiError
from FileTagServer.DBI.models import Folder, File, Tag
from FileTagServer.DBI.webconverter import WebConverter
from FileTagServer.REST.routing import reformat
from FileTagServer.WEB import content
from FileTagServer.WEB.app import WebsiteApp
from FileTagServer.WEB.streaming import serve_streamable_file, serve_streamable_buffer
from FileTagServer.WEB.routing import root_route, orphaned_files_route, folder_route, file_route, tag_route, file_data_route, file_preview_route


def get_icon(name: str) -> str:
    return f"bi-{name}"


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


def build_breadcrumbs(database: Database, name: str = "", url: str = "", path: str = "", add_self: bool = True):
    ancestry: List[Dict] = []
    if add_self:
        ancestry.append({'link': url, 'text': name})

    while True:
        path = dirname(path)
        try:
            parent_folder = database.folder.get_folder_by_path(path)
            d = {
                'link': reformat(folder_route, folder_id=parent_folder.id),
                'text': parent_folder.name
            }
            ancestry.append(d)
        except ApiError:
            break
    ancestry.append({'link': root_route, 'text': '~'})
    ancestry = ancestry[::-1]  # reverse order
    ancestry[-1]['current'] = True
    return ancestry


class WebJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(WebJSONEncoder, self).default(obj)


def build_folder_context(conv: WebConverter, name: str, description: str, ancestry: List[Dict], folders: List[Folder], files: List[File], tags: List[Tag], all_tags: List[Tag] = None):
    tag_lookup = {t.id: conv.tag(t) for t in all_tags} if all_tags else None

    folders = [conv.folder(f, tag_lookup) for f in folders] if folders else []
    files = [conv.file(f, tag_lookup) for f in files] if files else []
    # Use lookup to avoid reconverting, otherwise convert
    tags = ([conv.tag(t) for t in tags] if not tag_lookup else [tag_lookup[t.id] for t in tags]) if tags else []
    files_json = Util.json(files, encoder=WebJSONEncoder, exclude_unset=True, exclude_none=True)  # [f.json() for f in files]
    folders_json = Util.json(folders, encoder=WebJSONEncoder, exclude_unset=True, exclude_none=True)  # [f.json() for f in folders]

    files = Util.dict(files)
    for i, f in enumerate(files):
        f['file_index'] = i

    folders = Util.dict(folders)
    for i, f in enumerate(folders):
        f['folder_index'] = i

    tags = Util.dict(tags)

    return {
        'breadcrumbs': ancestry,
        'name': name,
        'desc': description,
        'files': files,
        'folders': folders,
        'tags': tags,

        'files_json': files_json,
        'folders_json': folders_json
    }


def build_file_context(conv: WebConverter, name: str, ancestry: List[Dict], file: File, all_tags: List[Tag] = None):
    tag_lookup = {t.id: conv.tag(t) for t in all_tags} if all_tags else None

    file = conv.file(file, tag_lookup) if file else None
    # Use lookup to avoid reconverting, otherwise convert
    # tags = ([conv.tag(t) for t in tags] if not tag_lookup else [tag_lookup[t.id] for t in tags]) if tags else []

    file = Util.dict(file)
    # folders = Util.dict(folders)
    # tags = Util.dict(tags)

    return {
        'breadcrumbs': ancestry,
        'name': name,
        # 'desc': description,
        'file': file,
        # 'folders': folders,
        # 'tags': tags,
    }


def add_routes(app: WebsiteApp):
    def __folder(context: Dict, list_view: bool = True):
        template_name = "list" if list_view else "table"
        path = app.local_pathing.html / f"folder/{template_name}.html"
        html = app.renderer.render_path(path, **context)
        return HTMLResponse(html)

    @app.get(root_route)
    def _root_folder():
        folders: List[Folder] = app.database.folder.get_root_folders()
        ancestry = build_breadcrumbs(app.database, add_self=False)  # Builds root only
        files = None  # get_orphaned_files()
        tags = None
        context = build_folder_context(app.webconv, "Root", None, ancestry, folders, files, tags)
        if app.database.file.has_orphaned_files():
            orphaned_folder = {
                'name': 'Orphaned Files',
                'id': '-',
                'icon': get_folder_icon(),
                'page': orphaned_files_route
            }
            context['folders'].append(orphaned_folder)
        return __folder(context)

    @app.get(folder_route)
    def _sub_folder(folder_id: int):
        folder = app.database.folder.get_folder(folder_id)
        subfolders: List[Folder] = app.database.folder.get_folders(folder.folders)
        files = app.database.file.get_files(folder.files)

        all_tags = app.webconv.collect_nested_tags(folder, subfolders, files)
        tag_lookup = app.database.tag.get_tags(all_tags)
        tags = [tag_lookup[tag_id] for tag_id in folder.tags] if folder.tags else None

        ancestry = build_breadcrumbs(app.database, folder.name, reformat(folder_route, folder_id=folder_id), folder.path)
        context = build_folder_context(app.webconv, folder.name, folder.description, ancestry, subfolders, files, tags, tag_lookup)
        return __folder(context)

    @app.get(orphaned_files_route)
    def _orphaned_file_folder():
        folder = None
        subfolders = None
        files = app.database.file.get_orphaned_files()

        all_tags = app.webconv.collect_nested_tags(folder, subfolders, files)
        tag_lookup = app.database.tag.get_tags(all_tags)
        tags = None

        ancestry = build_breadcrumbs(app.database, "Orphaned Files", orphaned_files_route)
        context = build_folder_context(app.webconv, "Orphaned Files", "Files with no parent folder.", ancestry, subfolders, files, tags, tag_lookup)
        return __folder(context)

    def __file(context: Dict):#, list_view: bool = True):
        template_name = "page"# "list" if list_view else "table"
        path = app.local_pathing.html / f"file/{template_name}.html"
        html = app.renderer.render_path(path, **context)
        return HTMLResponse(html)

    @app.get(file_route)
    def _file(file_id: int):
        file = app.database.file.get_file(file_id)
        tag_lookup = app.database.tag.get_tags(file.tags or [])
        ancestry = build_breadcrumbs(app.database, file.name, reformat(file_route, file_id=file_id), file.path)
        context = build_file_context(app.webconv, file.name, ancestry, file, tag_lookup)
        return __file(context)

    @app.get(file_preview_route)
    def _file_preview(file_id: int, range: Optional[str] = Header(None)):
        file = app.database.file.get_file(file_id)
        if content.supports_preview(file.mime):
            preview_path = app.previews.get_preview_path(file)
            if not preview_path.exists():
                app.previews.generate_preview(file)
            if preview_path.exists():
                return serve_streamable_file(str(preview_path), range)
            broken = app.local_pathing.img / "preview/broken.svg"
            return serve_streamable_file(str(broken), range)
        else:
            missing = app.local_pathing.img / "preview/missing.svg"
            return serve_streamable_file(str(missing), range)
