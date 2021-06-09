from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class Tag(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    count: Optional[int] = 0


class WebTag(Tag):
    page: Optional[str] = None


class RestTag(Tag):
    id: Optional[int] = None

    def as_response(self) -> 'RestTag':
        return RestTag(**self.dict())


class File(BaseModel):
    id: int
    path: str
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Tag]] = Field(default_factory=lambda: [])

    def as_response(self, fields=None, tag_fields=None) -> 'RestFile':
        fields = set(fields) if fields else None
        d = self.dict(include=fields)
        r = RestFile.construct(fields, **d)
        r_fixed = r.copy(include=fields)
        return r_fixed


class WebFile(File):
    page: Optional[str] = None
    tags: Optional[List[WebTag]] = Field(default_factory=lambda: [])
    preview: Optional[Dict[str, Any]] = None


#
class RestFile(File):
    id: Optional[int] = None
    path: Optional[str] = None
    tags: Optional[List[RestTag]] = Field(default_factory=lambda: [])
