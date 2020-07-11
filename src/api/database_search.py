# Convert String to Boolean Search
from typing import List, Tuple, Dict
import src.util.db_util as DbUtil

# Google uses - for NOT and OR for or, AND is probably inferred since i didnt see anything
from src.util import db_util

SEARCH_NOT = '-'
SEARCH_AND = ''
SEARCH_OR = '~'
# NOT SUPPORTED YET
SEARCH_GROUP_START = '('
SEARCH_GROUP_END = ')'
SEARCH_GROUP_LITERAL = '"'


def create_search_query(requests: Dict[str, str]):
    result_query = ""

    def append_query(sub_query, join_type="INTERSECT"):
        nonlocal result_query
        if sub_query is None:
            return
        if result_query != "":
            result_query += f" {join_type}"
        result_query += " " + sub_query

    tags = requests.get('tags', None)
    if tags is not None and len(tags) > 0:
        append_query(create_page_tag_query(create_simple_search_groups(tags)))

    include_untagged = requests.get('untagged', False)
    if include_untagged:
        append_query(create_untagged_query(), "UNION")

    append_query(create_page_info_query(requests))


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


def create_page_tag_query(groups: Tuple[List[str], List[str], List[str]]):
    ors, ands, nots = groups
    select_query = "SELECT page_id from tag_map left join tag on tag_map.tag_id = tag.id"
    result_query = ""
    require_intersect = False
    if ors is not None and len(ors) > 0:
        if require_intersect:
            result_query += " INTERSECT"
        result_query += f" {select_query} where tag.name IN {DbUtil.create_entry_string(ors)}"
        require_intersect = True
    if nots is not None and len(nots) > 0:
        if require_intersect:
            result_query += " INTERSECT"
        result_query += f" {select_query}"
        result_query += " EXCEPT"
        result_query += f" {select_query} where tag.name IN {DbUtil.create_entry_string(nots)}"
        require_intersect = True
    if ands is not None and len(ands) > 0:
        for single_and in ands:
            if require_intersect:
                result_query += " INTERSECT"
            result_query += f" {select_query} where tag.name = {DbUtil.sanitize(single_and)}"
            require_intersect = True
    if result_query == "":
        return None
    return result_query


def create_untagged_query():
    select_query = "SELECT page.id from file_page left join tag_map on tag_map.page_id= page.id left join tag on tag_map.tag_id = tag.id"
    untagged_query = " where tag_map.tag_id is NULL"
    result_query = select_query + untagged_query
    return result_query


def create_page_info_query(requests: Dict[str, str]):
    select_query = "SELECT page_id from file_page left join file on file.id=file_page.file_id"
    result_query = ""

    def list_helper(request_name, table_key):
        nonlocal result_query
        allowed = requests.get(request_name, None)
        if allowed is not None:
            formatted = db_util.create_entry_string(allowed)
            if result_query != "":
                result_query += " AND"
            result_query += f" {table_key} in {formatted}"

    list_helper('extensions', 'file.extension')
    list_helper('file_ids', 'file.id')
    list_helper('page_ids', 'page.id')
    if result_query == "":
        return None
    return select_query + result_query
