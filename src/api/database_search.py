# Convert String to Boolean Search
from typing import List, Tuple
import src.util.db_util as DbUtil

# Google uses - for NOT and OR for or, AND is probably inferred since i didnt see anything
SEARCH_NOT = '-'
SEARCH_AND = ''
SEARCH_OR = '~'
# NOT SUPPORTED YET
SEARCH_GROUP_START = '('
SEARCH_GROUP_END = ')'
SEARCH_GROUP_LITERAL = '"'


# Or / And / Not
def create_simple_search_groups(search: List[str]) -> (List[str], List[str], List[str]):
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


def create_query_from_search_groups(groups: Tuple[List[str], List[str], List[str]]):
    ors, ands, nots = groups
    select_query = "SELECT page_id from tag_map left join tag on tag_map.tag_id = tag.id"
    result_query = ""
    require_intersect = False
    if ors is not None and len(ors) > 0:
        if require_intersect:
            result_query += " INTERSECT"
        result_query += f" {select_query} where tag.name IN {DbUtil.to_sql_list(ors)}"
        require_intersect = True
    if nots is not None and len(nots) > 0:
        if require_intersect:
            result_query += " INTERSECT"
        result_query += f" {select_query}"
        result_query += " EXCEPT"
        result_query += f" {select_query} where tag.name IN {DbUtil.to_sql_list(nots)}"
        require_intersect = True
    if ands is not None and len(ands) > 0:
        for single_and in ands:
            if require_intersect:
                result_query += " INTERSECT"
            result_query += f" {select_query} where tag.name = {DbUtil.sanitize(single_and)}"
            require_intersect = True
    return result_query
