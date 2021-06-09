from typing import List, Optional
from pydantic import BaseModel, Field


class Tag(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    count: Optional[int] = 0

class TagResponse(Tag):
    id: Optional[int] = None

    def as_response(self) -> 'TagResponse':
        return TagResponse(**self.dict())

class File(BaseModel):
    id: int
    path: str
    mime: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Tag]] = Field(default_factory=lambda: [])

    def as_response(self, fields=None, tag_fields=None) -> 'FileResponse':
        fields = set(fields) if fields else None
        d = self.dict(include=fields)
        r = FileResponse.construct(fields, **d)
        r_fixed = r.copy(include=fields)
        return r_fixed


#
class FileResponse(File):
    id: Optional[int] = None
    path: Optional[str] = None
    tags: Optional[List[TagResponse]] = Field(default_factory=lambda: [])
