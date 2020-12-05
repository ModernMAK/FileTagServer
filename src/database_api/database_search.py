# Convert String to Boolean Search
from typing import List, Tuple

import src.util.db_util as DbUtil
# Google uses - for NOT and OR for or, AND is probably inferred since i didnt see anything
from src.database_api.clients import FileClient, FileTagMapClient, TagClient, FileTable, TagTable, FileTagMapTable

SEARCH_NOT = '-'
SEARCH_AND = ''
SEARCH_OR = '~'
# NOT SUPPORTED YET
SEARCH_GROUP_START = '('
SEARCH_GROUP_END = ')'
SEARCH_GROUP_LITERAL = '"'
SimpleSearchGroups = Tuple[List[str], List[str], List[str]]


class SqliteQueryBuidler:
    def __init__(self):
        self.parts = []

    @property
    def query(self) -> str:
        return " ".join(self.parts)

    def flush(self) -> str:
        result = self.query
        self.parts.clear()
        return result

    def Select(self, *items: str, mode: str = None) -> 'SqliteQueryBuidler':
        if mode is not None:
            mode = mode.upper()
            part = f"SELECT {mode} {' '.join(items)}"
        else:
            part = f"SELECT {' '.join(items)}"
        self.parts.append(part)
        return self

    def From(self, table: str) -> 'SqliteQueryBuidler':
        part = f"FROM {table}"
        self.parts.append(part)
        return self

    def Join(self, table: str, mode: str = None):
        part = f"JOIN {table}"
        if mode is not None:
            mode = mode.upper()
            part = f"{mode} {part}"
        self.parts.append(part)
        return self

    def On(self, expr):
        part = f"ON {expr}"
        self.parts.append(part)
        return self

    def Raw(self, sql):
        self.parts.append(sql)
        return self

    def Where(self, expr):
        part = f"WHERE {expr}"
        self.parts.append(part)
        return self

    def In(self, expr):
        part = f"IN {expr}"
        self.parts.append(part)
        return self

    def Not(self):
        self.parts.append("NOT")
        return self

    def Intersect(self, query):
        part = f"INTERSECT {query}"
        self.parts.append(part)
        return self


    def Limit(self, limit):
        part = f"LIMIT {limit}"
        self.parts.append(part)
        return self

    def Offset(self, offset):
        part = f"OFFSET {offset}"
        self.parts.append(part)
        return self


# Or / And / Not
def create_simple_search_groups(search: List[str]) -> SimpleSearchGroups:
    nots = []
    ands = []
    ors = []
    for item in search:
        if item[0] == SEARCH_NOT:
            nots.append(item[1:])
        elif item[0] == SEARCH_OR:
            ors.append(item[1:])
        elif item[0] == SEARCH_AND:
            ands.append(item[1:])
        else:
            ands.append(item)
    return ors, ands, nots


def create_query_from_search_groups(groups: SimpleSearchGroups):
    ors, ands, nots = groups
    query = SqliteQueryBuidler()

    select_query = query \
        .Select(FileTable.id_qualified) \
        .From(FileTable.table) \
        .Join(FileTagMapTable.table, mode="Left") \
        .On(f"{FileTable.id_qualified} = {FileTagMapTable.file_id_qualified}") \
        .Join(TagTable.table, mode="Left") \
        .On(f"{FileTagMapTable.tag_id_qualified} = {TagTable.id_qualified}") \
        .flush()

    # "SELECT file.id from file left join file_tag on file.id = file_Tag.file_id left join tag on file_tag.tag_id = tag.id"
    parts = []
    if ors is not None and len(ors) > 0:
        part = query \
            .Raw(select_query) \
            .Where(TagClient.name_column_qualified())\
            .In(DbUtil.create_entry_string(ors))
        parts.append(part)
        # f"{select_query} where tag.name IN {DbUtil.create_entry_string(ors)}"
    if nots is not None and len(nots) > 0:
        part = query\
            .Raw(select_query)\
            .Where(TagClient.name_column_qualified())\
            .Not()\
            .In(DbUtil.create_entry_string(nots))

        # part = f"{select_query} EXCEPT {select_query} where tag.name IN {DbUtil.create_entry_string(nots)}"
        parts.append(part)
    if ands is not None and len(ands) > 0:
        for single_and in ands:
            part = query.\
                Raw(select_query).\
                Where(f"{TagTable.name} = {DbUtil.sanitize(single_and)}").\
                flush()
            # part = f"{select_query} where tag.name = {DbUtil.sanitize(single_and)}"
            parts.append(part)

    # Merge parts
    query.Raw(parts[0])
    for part in range(1,len(parts)):
       query.Intersect(part)
    return query.flush()
