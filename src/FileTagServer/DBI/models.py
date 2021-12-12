from typing import Optional, List

from pydantic import BaseModel


class Tag(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    # Generated Fields
    count: Optional[int] = 0


class File(BaseModel):
    id: int
    path: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    mime: Optional[str] = None

    # Generated Fields
    parent_folder_id: Optional[int] = None
    tags: Optional[List[int]] = None


class Folder(BaseModel):
    id: int
    path: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    files: Optional[List[int]] = None
    folders: Optional[List[int]] = None
    tags: Optional[List[int]] = None


# WEB MODELS
class WebModel(BaseModel):
    page: str


class WebAncestor(WebModel):
    name: str


class WebAncestryModel:
    ancestry: Optional[List[WebAncestor]] = None


class WebIcon(BaseModel):
    icon: str


class WebTag(Tag, WebModel):
    pass


class WebFile(File, WebModel, WebAncestryModel, WebIcon):
    preview: Optional[str] = None
    parent: Optional['WebFolder'] = None
    tags: Optional[List[WebTag]] = None


class WebFolder(Folder, WebModel, WebAncestryModel, WebIcon):
    files: Optional[List[WebFile]] = None
    folders: Optional[List['WebFolder']] = None
    tags: Optional[List[WebTag]] = None


# required
# __locals = list(locals().values())
# for m in __locals:
#     if isinstance(m, BaseModel):
#         m.update_forward_refs()
WebFolder.update_forward_refs()
Folder.update_forward_refs()
