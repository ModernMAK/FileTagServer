from typing import List, Optional, Union

from pydantic import BaseModel, validator, Field

from FileTagServer.DBI.common import SortQuery, validate_fields
from FileTagServer.DBI.models import File, Tag


class FilesQuery(BaseModel):
    sort: Optional[List[SortQuery]] = None
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    # Validators
    @validator('sort', each_item=True)
    def validate_sort(cls, value: SortQuery) -> SortQuery:
        # will raise error if failed
        validate_fields(value.field, File.__fields__)
        return value

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class FileTagQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class FileMetaArgs(BaseModel):
    size_bytes: Optional[int] = None
    hash_md5: Optional[str] = None
    date_created: Optional[int] = None
    date_modified: Optional[int] = None
    date_uploaded: Optional[int] = None
    date_updated: Optional[int] = None


class ModifyFileQuery(FileMetaArgs):
    id: int
    path: Optional[str] = None
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None


class SetFileQuery(FileMetaArgs):
    id: int
    # Optional[...] without '= None' means the field is required BUT can be none
    path: str
    mime: Optional[str]
    name: Optional[str]
    description: Optional[str]
    # Tags are special: a put query allows them to be optional, since they can be set at a seperate endpoint
    tags: Optional[List[int]] = None



class FileQuery(BaseModel):
    id: int
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self) -> FileTagQuery:
        return FileTagQuery(id=self.id, fields=self.tag_fields)


class CreateFileQuery(FileMetaArgs):
    path: str
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None

    def create_file(self, id: int, tags: List[Tag]) -> File:
        return File(id=id, path=self.path, mime=self.mime, name=self.name, description=self.description, tags=tags)


class SearchQuery(BaseModel):
    # AND
    required: Optional[List[Union['SearchQuery', str]]] = None
    # OR
    include: Optional[List[Union['SearchQuery', str]]] = None
    # NOT
    exclude: Optional[List[Union['SearchQuery', str]]] = None


class FileSearchQuery(BaseModel):
    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None
    sort: Optional[List[SortQuery]] = None
    search: Optional[SearchQuery] = None
    page: Optional[int] = Field(1, ge=1)

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)


class FilePathQuery(BaseModel):
    path: str

    fields: Optional[List[str]] = None
    tag_fields: Optional[List[str]] = None

    @validator('fields', each_item=True)
    def validate_fields(cls, value: str) -> str:
        return validate_fields(value, File.__fields__)

    @validator('tag_fields', each_item=True)
    def validate_tag_fields(cls, value: str) -> str:
        return validate_fields(value, Tag.__fields__)

    def create_tag_query(self, id: int) -> FileTagQuery:
        return FileTagQuery(id=id, fields=self.tag_fields)


class DeleteFileQuery(BaseModel):
    id: int


class FileDataQuery(BaseModel):
    id: int
    range: Optional[str] = None
