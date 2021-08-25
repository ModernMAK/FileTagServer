from typing import List

from FileTagServer.DBI.common import __connect, replace_kwargs
from FileTagServer.DBI.models import Tag
from FileTagServer.DBI.tag import queries


def get_tags(tag_ids: List[int]) -> List[Tag]:
    if not tag_ids:
        return []
    with __connect() as (conn, cursor):
        sql_placeholder = ", ".join(["?" for _ in range(len(tag_ids))])
        sql = replace_kwargs(queries.select_by_ids, tag_ids=sql_placeholder)
        cursor.execute(sql, tag_ids)
        rows = cursor.fetchall()
        return [Tag(**dict(row)) for row in rows]
