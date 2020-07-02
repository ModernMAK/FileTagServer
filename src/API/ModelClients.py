import os
import sqlite3

from typing import Dict, Union, List, Tuple, Any, Set

from src.DbUtil import Conwrapper, create_entry_string, create_value_string, sanitize
import src.API.Models as Models


def tuple_to_dict(value: Union[None, Tuple, List[Tuple]], mapping: Union[Tuple, List]):
    if value is None:
        return {}
    if not isinstance(value, List):
        result = {}
        for i in range(len(mapping)):
            v = value[i]
            m = mapping[i]
            result[m] = v
        return result
    else:
        result = []
        for row in value:
            temp = {}
            for i in range(len(mapping)):
                v = row[i]
                m = mapping[i]
                temp[m] = v
            result.append(temp)
        return result


def get_unique_helper(rows: List[Dict[str, Any]], key: str) -> Set[Any]:
    unique = set()
    for row in rows:
        unique.add(row[key])
    return unique


def group_dicts_on_key(list_dict: List[Dict[Any, Any]], key: str) -> Dict[Any, List[Dict[Any, Any]]]:
    result = {}
    for d in list_dict:
        k = d[key]
        if k in result:
            result[k].append(d)
        else:
            result[k] = [d]
    return result


def create_tag_table(tags: List[Models.Tag]) -> Dict[int, Models.Tag]:
    d = {}
    for tag in tags:
        d[tag.id] = tag
    return d


def create_page_table(tags: List[Models.Page]) -> Dict[int, Models.Page]:
    d = {}
    for tag in tags:
        d[tag.page_id] = tag
    return d


def create_file_table(files: List[Models.File]) -> Dict[int, Models.File]:
    d = {}
    for file in files:
        d[file.file_id] = file
    return d


class BaseClient:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path')

    def _perform_select(self, select_query: str):
        # if os.path.exists(self.db_path):
        #     print(f"EXISTS: {self.db_path}")
        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(select_query)
                return cursor.fetchall()
        except sqlite3.DatabaseError as e:
            print(str(e))
            return None


class Page(BaseClient):
    def get(self, **kwargs) -> List[Models.Page]:
        # GATHER ARGS
        page_size = kwargs.get('page_size', None)
        offset = kwargs.get('offset', None)
        requested_ids = kwargs.get('ids', None)

        # ASSEMBLE QUERY
        query = f"SELECT id, name, description from page"
        if any(v is not None for v in [requested_ids]):
            query += " where"
            append_or = False
            if requested_ids is not None:
                if append_or:
                    query += " or"
                query += f" id in {create_entry_string(requested_ids)}"
                append_or = True

        if page_size is not None:
            query += f" LIMIT {int(page_size)}"
        if offset is not None:
            query += f" OFFSET {int(offset)}"

        # PERFORM QUERY
        rows = self._perform_select(query)

        # FORMAT RESULTS
        mapping = ("id", "name", "description")
        formatted = tuple_to_dict(rows, mapping)

        # GATHER ADDITIONAL TABLES ~ TAGS
        unique_pages = get_unique_helper(formatted, 'id')
        tag_client = Tag(db_path=self.db_path)
        formatted_tag_map = tag_client.get_map(page_ids=unique_pages)
        unique_tags = formatted_tag_map.keys()
        tag_table = create_tag_table(tag_client.get(ids=unique_tags))

        # RETURN ASSEMBLED MODELS
        results = []
        for row in formatted:
            page = Models.Page(**row)
            page.tags = []
            if page.page_id in formatted_tag_map:
                for tag_id in formatted_tag_map[page.page_id]:
                    page.tags.append(tag_table[tag_id])
            results.append(page)
        return results


class FilePage(BaseClient):
    def get(self, **kwargs) -> List[Models.FilePage]:
        # GATHER ARGS
        page_size = kwargs.get('page_size', None)
        offset = kwargs.get('offset', None)
        requested_ids = kwargs.get('ids', None)

        # ASSEMBLE QUERY
        query = f"SELECT id, page_id, file_id from file_page"
        if any(v is not None for v in [requested_ids]):
            query += " where"
            append_or = False
            if requested_ids is not None:
                if append_or:
                    query += " or"
                query += f" file_page.id in {create_entry_string(requested_ids)}"
                append_or = True

        if page_size is not None:
            query += f" LIMIT {int(page_size)}"
        if offset is not None:
            query += f" OFFSET {int(offset)}"

        # PERFORM QUERY
        rows = self._perform_select(query)

        # FORMAT RESULTS
        mapping = ("id", "page_id", "file_id")
        formatted = tuple_to_dict(rows, mapping)

        # GATHER ADDITIONAL TABLES ~ Page
        unique_page_ids = get_unique_helper(formatted, 'page_id')
        page_client = Page(db_path=self.db_path)
        unique_pages = page_client.get(ids=unique_page_ids)
        page_table = create_page_table(unique_pages)

        # GATHER ADDITIONAL TABLES ~ File
        unique_file_ids = get_unique_helper(formatted, 'file_id')
        file_client = File(db_path=self.db_path)
        unique_files = file_client.get(ids=unique_file_ids)
        file_table = create_file_table(unique_files)

        # RETURN ASSEMBLED MODELS
        results = []
        for row in formatted:
            page_id, file_id = row['page_id'], row['file_id']
            page = page_table[page_id]
            file = file_table[file_id]
            base = page.to_dictionary()
            base.update(row)
            base['file'] = file
            results.append(Models.FilePage(**base))
        return results


class Tag(BaseClient):
    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_names = create_entry_string(kwargs.get('names', []))
        allowed_pages = create_entry_string(kwargs.get('page_ids', []))
        allowed_classes = create_entry_string(kwargs.get('classes', []))
        query = f"SELECT tag.id, name, description, class, count(page_id) as count from tag" \
                f" left join tag_map on tag.id = tag_map.tag_id" \
                f" where tag.id in {allowed_ids} or name in {allowed_names} or class in {allowed_classes}" \
                f" or tag_map.page_id in {allowed_pages}" \
                f" group by tag.id"
        rows = self._perform_select(query)
        mapping = ("id", "name", 'description', 'class', 'count')
        formatted = tuple_to_dict(rows, mapping)
        results = []
        for row in formatted:
            results.append(Models.Tag(**row))
        return results

    def get_map(self, **kwargs) -> Dict[int, List[int]]:
        allowed_pages = create_entry_string(kwargs.get('page_ids', []))
        query = f"SELECT tag_map.page_id, tag_map.id from tag_map where tag_map.page_id in {allowed_pages}"
        rows = self._perform_select(query)
        mapping = ("page_id", "tag_id")
        formatted = tuple_to_dict(rows, mapping)
        result = {}
        for row in formatted:
            page = row['page_id']
            tag = row['tag_id']
            if page not in result:
                result[page] = []
            result[page].append(tag)
        return result


class File(BaseClient):
    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        query = f"SELECT id, path, extension from file" \
                f" where id in {allowed_ids}"

        rows = self._perform_select(query)
        mapping = ("id", "path", 'extension')
        formatted = tuple_to_dict(rows, mapping)
        results = []
        for row in formatted:
            results.append(Models.File(**row))
        return results
