# from os.path import split
# from typing import Union, List, Tuple, Optional
#
# from fastapi import Header
# from starlette.responses import HTMLResponse
#
# from FileTagServer.DBI.file import old_file as file_api
# from FileTagServer.DBI.common import Util
# from FileTagServer.DBI.file.old_file import FilesQuery, FileQuery
# from FileTagServer.DBI.folder.old_folder import get_root_folders, FolderQuery, get_folder
# from FileTagServer.DBI.old_models import File, WebTag, WebFile, Tag, Folder
# from FileTagServer.REST.routing import reformat
# from FileTagServer.WEB.common import web_app, render, serve_streamable
# from FileTagServer.WEB.routing import files_route, file_route, tag_route, file_data_route, file_edit_route, \
#     file_edit_submit_route, folder_route, root_route, orphaned_files_route
#
#
# def dummy():
#     pass
#
#
# def build_context(name: str, description: str, folders: List[Folder], files: List[File], tags: List[Tag]):
#     folders = Util.dict(folders)
#     for f in folders:
#         f['page'] = reformat(folder_route, folder_id=f['id'])
#
#     files = Util.dict(files)
#     for f in files:
#         f['page'] = reformat(file_route, file_id=f['id'])
#
#     tags = Util.dict(tags)
#     for t in tags:
#         t['page'] = reformat(tag_route, tag_id=t['id'])
#
#     return {
#         'name': name,
#         'desc': description,
#         'files': files,
#         'folders': folders,
#         'tags': tags
#     }
#
#
# @web_app.get(root_route)
# def root():
#     folders: List[Folder] = get_root_folders()
#     files = []  # get_orphaned_files()
#     tags = []
#     context = build_context("Root", None, folders, files, tags)
#     orphaned_folder = {
#         'name': 'Orphaned Files',
#         'id': '-',
#         'page': orphaned_files_route
#     }
#     context['folders'].append(orphaned_folder)
#     html = render("../static/html/folder/table.html", **context)
#     return HTMLResponse(html)
#
# @web_app.get(folder_route)
# def folder(folder_id:int):
#     q = FolderQuery(id=folder_id)
#     f:Folder = get_folder(q)
#     folders = f.subfolders
#     files = f.files
#     tags = f.tags
#     context = build_context(f.name, f.description, folders, files, tags)
#     # context['folders'].append(orphaned_folder)
#     html = render("../static/html/folder/table.html", **context)
#     return HTMLResponse(html)
#
#
# def add_file_tag_page_url(files: Union[List[WebFile], WebFile]) -> Union[List[WebFile], WebFile]:
#     def add_url(file: WebFile) -> WebFile:
#         file.tags = add_tag_page_url(file.tags)
#         return file
#
#     return [add_url(f) for f in files] if isinstance(files, (List, Tuple)) else add_url(files)
#
#
# def add_file_preview(files: Union[List[WebFile], WebFile]) -> Union[List[WebFile], WebFile]:
#     def add_preview(file: WebFile) -> WebFile:
#         if file.mime is None:
#             return file
#         f, _ = split(file.mime)
#         file.preview = {f: {'url': reformat(file_data_route, file_id=file.id)}}
#         return file
#
#     return [add_preview(f) for f in files] if isinstance(files, (List, Tuple)) else add_preview(files)
#
#
# def add_file_page_url(files: Union[List[WebFile], WebFile]) -> Union[List[WebFile], WebFile]:
#     def add_url(file: WebFile) -> WebFile:
#         file.page = reformat(file_route, file_id=file.id)
#         file.edit_page = reformat(file_edit_route, file_id=file.id)
#         return file
#
#     return [add_url(f) for f in files] if isinstance(files, (List, Tuple)) else add_url(files)
#
#
# def add_tag_page_url(tags: Union[List[WebTag], WebTag]) -> Union[List[WebTag], WebTag]:
#     def add_url(tag: WebTag) -> WebTag:
#         tag.page = reformat(tag_route, tag_id=tag.id)
#         return tag
#
#     return [add_url(f) for f in tags] if isinstance(tags, (List, Tuple)) else add_url(tags)
#
#
# def fix_files(files: Union[List[File], File]) -> Union[List[WebFile], WebFile]:
#     files = [WebFile(**f.dict()) for f in files] if isinstance(files, (List, Tuple)) else WebFile(**files.dict())
#     files = add_file_page_url(files)
#     files = add_file_tag_page_url(files)
#     files = add_file_preview(files)
#     return files
#
#
# @web_app.get(folder_route)
# def folder():
#     q = FoldersQuery()
#     folders = file_api.get_root_folders()
#     files = fix_files(files)
#     sort_file_tags(files)
#     results = Util.dict(files)
#     context = {'results': results}
#     html = render("../static/html/file/list.html", **context)
#     return HTMLResponse(html)
#
#
# @web_app.get(files_route + "/grid")
# def file_grid():
#     q = FilesQuery()
#     files = file_api.get_files(q)
#     files = fix_files(files)
#     results = Util.dict(files)
#     context = {'results': results}
#     html = render("../static/html/file/grid.html", **context)
#     return HTMLResponse(html)
#
#
# @web_app.get(file_route)
# def file(file_id: int):
#     q = FileQuery(id=file_id)
#     file = file_api.get_file(q)
#     file = fix_files(file)
#     sort_file_tags(file)
#     result = Util.dict(file)
#     context = {'result': result}
#     html = render("../static/html/file/page.html", **context)
#     return HTMLResponse(html)
#
#
# def sort_file_tags(file: Union[File, List[File]]) -> Union[File, List[File]]:
#     def do_sort(f: File) -> File:
#         def get_name(tag: Tag) -> str:
#             return tag.name
#
#         f.tags.sort(key=get_name)
#         return f
#
#     return [do_sort(fi) for fi in file] if isinstance(file, (List, Tuple)) else do_sort(file)
#
#
# @web_app.get(file_edit_route)
# def file_edit(file_id: int):
#     q = FileQuery(id=file_id)
#     file = file_api.get_file(q)
#     file = fix_files(file)
#     sort_file_tags(file)
#     result = Util.dict(file)
#     action_url = reformat(file_edit_submit_route, file_id=file_id)
#     context = {'result': result, 'form': {'action': action_url}}
#     html = render("../static/html/file/page_edit.html", **context)
#     return HTMLResponse(html)
#
#
# @web_app.get(file_data_route)
# def file_data(file_id: int, range: Optional[str] = Header(None)):
#     path = file_api.get_file_path(file_id)
#     return serve_streamable(path, range)
