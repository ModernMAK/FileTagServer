from typing import List, Optional
from pydantic import BaseModel, Field


class Tag(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    count: Optional[int] = 0


class File(BaseModel):
    id: int
    path: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Tag]] = Field(default_factory=lambda: [])
