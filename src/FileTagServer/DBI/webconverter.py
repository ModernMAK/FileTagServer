from typing import Optional, List, Dict, Set

from FileTagServer.DBI.models import File, Folder, WebTag, Tag, WebFile, WebFolder
from FileTagServer.REST.routing import reformat
from FileTagServer.WEB import content


class WebConverter:
    def __init__(self, folder_route, get_folder_icon, file_route, file_preview_route, get_file_icon, tag_route):
        self.file_preview_route = file_preview_route
        self.folder_route = folder_route
        self.folder_icon = get_folder_icon
        self.file_route = file_route
        self.file_icon = get_file_icon
        self.tag_route = tag_route

    @staticmethod
    def collect_file_tags(files: List[File]) -> Set[int]:
        tags = set()
        for file in files:
            if file.tags:
                for tag in file.tags:
                    tags.add(tag)
        return tags

    @staticmethod
    def collect_folder_tags(folders: List[Folder]) -> Set[int]:
        tags = set()
        for folder in folders:
            if folder.tags:
                for tag in folder.tags:
                    tags.add(tag)
        return tags

    @staticmethod
    def collect_folder_files(folders: List[Folder]) -> Set[int]:
        files = set()
        for folder in folders:
            if folder.tags:
                for file in folder.files:
                    files.add(file)
        return files

    @classmethod
    def collect_nested_tags(cls, folder: Optional[Folder], subfolders: Optional[List[Folder]], files: Optional[List[File]]) -> Set[int]:
        folder_tags = folder.tags if folder else []
        folder_tags = folder_tags or []

        subfolder_tags = cls.collect_folder_tags(subfolders) if subfolders else []
        subfolder_tags = subfolder_tags or []

        file_tags = cls.collect_file_tags(files) if files else []
        file_tags = file_tags or []

        return set(folder_tags).union(file_tags).union(subfolder_tags)

    @staticmethod
    def collect_folder_subfolders(folders: List[Folder]) -> Set[int]:
        subfolders = set()
        for folder in folders:
            if folder.tags:
                for subfolder in folder.folders:
                    subfolders.add(subfolder)
        return subfolders

    def folder(self, folder: Folder, tag_lookup: Dict[int, 'WebTag'] = None) -> 'WebFolder':
        tags = (None if not tag_lookup else [tag_lookup[t] for t in folder.tags]) if folder.tags else None
        if tags:
            tags.sort()
        kwargs = folder.dict(exclude={"files", "folders", "tags"})

        return WebFolder(
            page=reformat(self.folder_route, folder_id=folder.id),
            icon=self.folder_icon(),
            files=None,  # [self.file(file, tag_lookup) for file in folder.f]
            folders=None,
            tags=tags,
            **kwargs
        )
    def __is_previewable(self, mimetype:str):
        return True
        # We rely on serving preview to serve a default if we aren't previewable
        return content.supports_preview(mimetype)


    def file(self, file: File, tag_lookup: Dict[int, 'WebTag'] = None) -> 'WebFile':
        tags = (None if not tag_lookup else [tag_lookup[t] for t in file.tags]) if file.tags else None
        if tags:
            tags.sort(key=lambda tag: tag.name)

        kwargs = file.dict(exclude={"tags"})
        preview = None
        if self.__is_previewable(file.mime):
            preview = reformat(self.file_preview_route, file_id=file.id)
        return WebFile(
            preview = preview,
            page=reformat(self.file_route, file_id=file.id),
            icon=self.file_icon(file.mime),
            tags=tags,
            **kwargs
        )

    def tag(self, tag: Tag) -> 'WebTag':
        kwargs = tag.dict()
        return WebTag(
            page=reformat(self.tag_route, tag_id=tag.id),
            **kwargs,
        )
