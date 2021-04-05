from typing import Optional, List, Union

from pydantic import Field, BaseModel

from src.api.models import File, Tag
from src.rest import routes


class RestTagUrls(BaseModel):
    self: str


class RestTag(Tag):
    urls: Optional[RestTagUrls] = None

    @staticmethod
    def from_tag(tags: Union[List[Tag], Tag]) -> Union[List['RestTag'], 'RestTag']:
        def reformat(t: Tag) -> 'RestTag':
            urls = RestTagUrls(
                self=routes.file.path(root="http://localhost:8000",file_id=t.id)
            )
            return RestTag(
                id=t.id,
                name=t.name,
                description=t.description,
                urls=urls
            )

        if isinstance(tags, Tag):  # single
            return reformat(tags)
        else:
            return [reformat(tag) for tag in tags]


class RestFileUrls(BaseModel):
    self: str
    tags: str
    bytes: str


class RestFile(File):
    tags: Optional[List[RestTag]] = Field(default_factory=lambda: [])
    urls: Optional[RestFileUrls] = None

    @staticmethod
    def from_file(files: Union[List[File], File]) -> Union[List['RestFile'], 'RestFile']:
        def reformat(f:File) -> 'RestFile':
            tags = RestTag.from_tag(f.tags)
            urls = RestFileUrls(
                self=routes.file.path(root="http://localhost:8000", file_id=f.id),
                tags=routes.file_tags.path(root="http://localhost:8000",file_id=f.id),
                bytes=routes.file_bytes.path(root="http://localhost:8000",file_id=f.id),
            )
            return RestFile(
                id=f.id,
                path=f.path,
                name=f.name,
                description=f.description,
                tags=tags,
                urls=urls
            )

        if isinstance(files,File): #single
            return reformat(files)
        else:
            return [reformat(file) for file in files]


