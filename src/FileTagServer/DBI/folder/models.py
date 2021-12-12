from typing import List, Optional, Union

from pydantic import BaseModel, validator, Field

from FileTagServer.DBI.common import SortQuery, validate_fields
from FileTagServer.DBI.models import Folder, Tag


class FoldersQuery(BaseModel):
    sort: Optional[List[SortQuery]] = None
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    # Validators
    @validator('sort', each_item=True)
    def validate_sort(cls, value: SortQuery) -> SortQuery:
        # will raise error if failed
        validate_fields(value.field, Folder.__fields__)
        return value

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class FolderTagQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class ModifyFolderQuery(BaseModel):
    path: Optional[str] = None
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None


class FullModifyFolderQuery(ModifyFolderQuery):
    id: int


class SetFolderQuery(BaseModel):
    # Optional[...] without '= None' means the field is required BUT can be none
    path: str
    mime: Optional[str]
    name: Optional[str]
    description: Optional[str]
    # Tags are special: a put query allows them to be optional, since they can be set at a seperate endpoint
    tags: Optional[List[int]] = None


class FullSetFolderQuery(SetFolderQuery):
    id: int


class FolderQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self) -> FolderTagQuery:
        return FolderTagQuery(id=self.id, fields=self.tag_fields)


class FolderPathQuery(BaseModel):
    path: str

    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self, id: int) -> FolderTagQuery:
        return FolderTagQuery(id=id, fields=self.tag_fields)


class CreateFolderQuery(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None

    def create_folder(self, id: int, tags: List[Tag]) -> Folder:
        return Folder(id=id, path=self.path, name=self.name, description=self.description, tags=tags)


class SearchQuery(BaseModel):
    # AND
    required: Optional[List[Union['SearchQuery', str]]] = None
    # OR
    include: Optional[List[Union['SearchQuery', str]]] = None
    # NOT
    exclude: Optional[List[Union['SearchQuery', str]]] = None


class FolderSearchQuery(BaseModel):
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None
    sort: Optional[List[SortQuery]] = None
    search: Optional[SearchQuery] = None
    page: Optional[int] = Field(1, ge=1)

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, Folder.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)



class DeleteFolderQuery(BaseModel):
    id: int

class FolderDataQuery(BaseModel):
    id: int
    range: Optional[str] = None
