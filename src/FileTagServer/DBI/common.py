import json
from contextlib import contextmanager
from sqlite3 import Connection, Cursor, connect, Row
from typing import List, Tuple, Optional, Union, AbstractSet, Mapping, Any, Dict, Callable, Set

from pydantic import BaseModel

from FileTagServer import config
from FileTagServer.DBI.models import Tag, File


def read_sql_file(file: str, strip_terminal=False):
    with open(file, "r") as f:
        r = f.read()
        if strip_terminal and r[-1] == ';':
            return r[:-1]
        else:
            return r


def validate_fields(value: str, fields: Union[List[str], Dict[str, Any], Set[str]]) -> str:
    if value not in fields:
        quoted_fields = [f'\'{f}\'' for f in fields]
        raise ValueError(f"Field '{value}' not allowed! Allowed fields: {', '.join(quoted_fields)}")
    return value


def row_to_file(r: Row, *, tags: List[Tag] = None, tag_lookup: Dict[int, Tag] = None, ) -> File:
    r: Dict = dict(r)
    if tags:
        r['tags'] = tags
    elif r['tags'] is not None:
        if tag_lookup:
            f_tags = r['tags']
            f_tags = [int(tag_id) for tag_id in f_tags.split(",")]
            r['tags'] = [tag_lookup[id] for id in f_tags]
    else:
        r['tags'] = []
    return File(**r)


def row_to_tag(r: Row) -> Tag:
    r: Dict = dict(r)
    return Tag(**r)


@contextmanager
def __connect(path=None, **kwargs) -> Tuple[Connection, Cursor]:
    path = path or config.db_path
    with connect(path, **kwargs) as conn:
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        cursor.row_factory = Row
        yield conn, cursor


def initialize_database():
    with __connect() as (conn, cursor):
        dirs = ['file', 'tag', 'file_tag']
        for dir in dirs:
            sql_part = read_sql_file(f"static/sql/{dir}/create.sql")
            cursor.execute(sql_part)


IntStr = Union[int, str]
MappingIntStrAny = Mapping[IntStr, Any]
AbstractSetIntStr = AbstractSet[IntStr]
DictStrAny = Dict[str, Any]


class Util:
    ListOrModel = Union[List[BaseModel], BaseModel]
    ListOrDictStrAny = Union[List['DictStrAny'], 'DictStrAny']

    @staticmethod
    def copy(
            self: ListOrModel,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            update: 'DictStrAny' = None,
            deep: bool = False,
    ) -> ListOrModel:
        args = {k: v for k, v in locals().items() if k != 'self'}

        if isinstance(self, list):
            return [t.copy(**args) for t in self]
        return self.copy(**args)

    @staticmethod
    def dict(
            self: ListOrModel,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            by_alias: bool = False,
            skip_defaults: bool = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
    ) -> ListOrDictStrAny:
        args = {k: v for k, v in locals().items() if k != 'self'}

        if isinstance(self, list):
            return [t.dict(**args) for t in self]
        return self.dict(**args)

    @staticmethod
    def json(
            self: ListOrModel,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            by_alias: bool = False,
            skip_defaults: bool = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            encoder: Optional[Callable[[Any], Any]] = None,
            **dumps_kwargs: Any,
    ) -> str:
        # We also drop encoder, as these are all args for dict
        args = {k: v for k, v in locals().items() if k not in {'self', 'encoder', 'dumps_kwargs'}}
        # args.update(dumps_kwargs)

        # A hack; could use dict and then pump that into jsonbut I don't know if that will work with custom encoders
        if isinstance(self, list):
            as_dict = Util.dict(self, **args)
            return json.dumps(as_dict, default=encoder, **dumps_kwargs)
        else:
            return self.json(encoder=encoder, **args, **dumps_kwargs)


def parse_fields(fields: str) -> Optional[List[str]]:
    if fields is None:
        return None
    return fields.split(",")


class SortQuery(BaseModel):
    field: str
    ascending: bool = True

    def sql(self) -> str:
        return f"{self.field} {'ASC' if self.ascending else 'DESC'}"

    @staticmethod
    def list_sql(q: Union[List['SortQuery'], 'SortQuery']) -> str:
        if q is None:
            return ''
        parts = []
        if isinstance(q, list):
            for part in q:
                parts.append(part.sql())
        else:
            parts.append(q.sql())
        return ", ".join(parts)

    @staticmethod
    def parse_str(q: str) -> List['SortQuery']:
        if q is None:
            return None
        pairs = q.split(",")
        results = []
        for pair in pairs:
            asc = True
            name = pair.strip()
            if pair[0] == "+":
                asc = True
                name = pair[1:].strip()
            elif pair[0] == "-":
                asc = False
                name = pair[1:].strip()
            results.append(SortQuery(field=name, ascending=asc))
        return results

    def to_str(self) -> str:
        if self.ascending:
            return f"{self.field}"
        else:
            return f"-{self.field}"

    @staticmethod
    def list_to_str(q:List['SortQuery']) -> str:
        if q is None:
            return None
        parts = [p.to_str() for p in q]
        return ",".join(parts)


class AutoComplete(BaseModel):
    label: str
    value: str


def fields_to_str(fields:List[str]):
    if fields is None or len(fields) == 0:
        return None
    return ",".join(fields)
