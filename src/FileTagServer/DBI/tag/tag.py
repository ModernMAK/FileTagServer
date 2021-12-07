from typing import List

from FileTagServer.DBI.common import replace_kwargs, AbstractDBI
from FileTagServer.DBI.models import Tag
from FileTagServer.DBI.tag import queries


class TagDBI(AbstractDBI):
    def get_tags(self, tag_ids: List[int]) -> List[Tag]:
        if not tag_ids:
            return []
        if isinstance(tag_ids,set):
            tag_ids = list(tag_ids)

        with self.connect() as (conn, cursor):
            sql_placeholder = ", ".join(["?" for _ in range(len(tag_ids))])
            sql = replace_kwargs(queries.select_by_ids, tag_ids=sql_placeholder)
            cursor.execute(sql, tag_ids)
            rows = cursor.fetchall()
            return [Tag(**dict(row)) for row in rows]
