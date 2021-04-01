from typing import List, Dict


class Model:
    @classmethod
    def validate(cls, data: dict) -> bool:
        raise NotImplementedError()


class Tag(Model):
    id: int
    urls: Dict[str, str]
    name: str
    description: str
    count: str


class File(Model):
    id: int
    urls: Dict[str, str]
    path: str
    mime: str
    name: str
    description: str
    tags: List[Tag]
