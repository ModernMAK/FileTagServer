import sqlite3

from typing import Dict, Union, List

from src.api import database_search
from src.util import db_util
from src.util.db_util import Conwrapper, create_entry_string, create_value_string, sanitize
import src.api.models as Models
import src.util.collection_util as collection_util


class BaseClient:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path')

    def _perform_select(self, select_query: str):
        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(select_query)
                return cursor.fetchall()
        except sqlite3.DatabaseError as e:
            print(str(e))
            return None

    def _perform_count(self, select_query: str):
        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(f"SELECT COUNT(*) FROM ({select_query})")
                count, = cursor.fetchone()  # COMMA IS IMPORTANT, untuples the fetch call
                return count
        except sqlite3.DatabaseError as e:
            print(str(e))
            return None


class Page(BaseClient):
    def assemble_query(self, **kwargs):
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
        return query

    def get(self, **kwargs) -> List[Models.Page]:

        # PERFORM QUERY
        rows = self._perform_select(self.assemble_query(**kwargs))

        # FORMAT RESULTS
        mapping = ("id", "name", "description")
        formatted = collection_util.tuple_to_dict(rows, mapping)

        # GATHER ADDITIONAL TABLES ~ TAGS
        unique_pages = collection_util.get_unique_values_on_key(formatted, 'id')
        tag_client = Tag(db_path=self.db_path)
        formatted_tag_map = tag_client.get_map(page_ids=unique_pages)
        unique_tags = collection_util.get_unique_values(formatted_tag_map)
        tag_table = tag_client.get_table(ids=unique_tags)

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

    def get_lookup(self, **kwargs) -> Dict[int, Models.Page]:
        def get_key(page: Models.Page) -> int:
            return page.page_id

        return collection_util.create_lookup(self.get(**kwargs), get_key)

    def count(self, **kwargs) -> Union[None, int]:
        return self._perform_count(self.assemble_query(**kwargs))


class FilePage(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def assemble_query(self, **kwargs):
        # GATHER ARGS
        page_size = kwargs.get('page_size', None)
        offset = kwargs.get('offset', None)
        requested_ids = kwargs.get('ids', None)
        requested_page_ids = kwargs.get('page_ids', None)

        # ASSEMBLE QUERY
        query = f"SELECT id, page_id, file_id from file_page"
        if any(v is not None for v in [requested_ids, requested_page_ids]):
            query += " where"
            append_or = False
            if requested_ids is not None:
                if append_or:
                    query += " or"
                query += f" file_page.id in {create_entry_string(requested_ids)}"
                append_or = True
            if requested_page_ids is not None:
                if append_or:
                    query += " or"
                query += f" file_page.page_id in {create_entry_string(requested_page_ids)}"
                append_or = True

        if page_size is not None:
            query += f" LIMIT {int(page_size)}"
        if offset is not None:
            query += f" OFFSET {int(offset)}"
        return query

    def get(self, **kwargs) -> List[Models.FilePage]:

        # PERFORM QUERY
        rows = self._perform_select(self.assemble_query(**kwargs))

        # FORMAT RESULTS
        mapping = ("id", "page_id", "file_id")
        formatted = collection_util.tuple_to_dict(rows, mapping)

        # GATHER ADDITIONAL TABLES ~ Page
        unique_page_ids = collection_util.get_unique_values_on_key(formatted, 'page_id')
        page_client = Page(db_path=self.db_path)
        page_table = page_client.get_lookup(ids=unique_page_ids)

        # GATHER ADDITIONAL TABLES ~ File
        unique_file_ids = collection_util.get_unique_values_on_key(formatted, 'file_id')
        file_client = File(db_path=self.db_path)
        file_table = file_client.get_table(ids=unique_file_ids)

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

    def get_lookup(self, **kwargs) -> Dict[int, Models.FilePage]:
        def get_key(page: Models.FilePage) -> int:
            return page.file_page_id

        return collection_util.create_lookup(self.get(**kwargs), get_key)

    def count(self, **kwargs) -> Union[None, int]:
        return self._perform_count(self.assemble_query(**kwargs))

    def set_tags(self, file_page_id: int, tags: List[str]):
        # Leaving this here for now in case i need to find it again
        # necro-ed from commit #42638a95c77eb314d5c075c7bf69efeba83a0eca
        with Conwrapper(self.db_path) as (con, cursor):
            formatted_tag_list = create_entry_string(tags)
            # Get tag_ids to set
            cursor.execute(f"SELECT id FROM tag WHERE name IN {formatted_tag_list}")
            rows = cursor.fetchall()
            tag_id_list = db_util.convert_tuple_to_list(rows)
            formatted_tag_id_list = create_entry_string(tag_id_list)
            cursor.execute(
                f"DELETE FROM tag_map where page_id = {file_page_id} and tag_id NOT IN {formatted_tag_id_list}")
            pairs = []
            for tag_id in tag_id_list:
                pairs.append((file_page_id, tag_id))
            formatted_pairs = create_value_string(pairs)
            cursor.execute(f"INSERT OR IGNORE INTO tag_map (page_id, tag_id) VALUES {formatted_pairs}")
            con.commit()

    def set_page_values(self, id: int, name: str = None, desc: str = None):
        if all(v is None for v in [name, desc]):
            return

        query = f"UPDATE page SET"
        cols = []
        if name is not None:
            cols.append(f"name = {sanitize(name.strip())}")
        if desc is not None:
            cols.append(f"description = {sanitize(desc.strip())}")
        cols_as_str = ", ".join(cols)
        query += " " + cols_as_str + f" where id = {sanitize(id)}"
        with Conwrapper(self.db_path) as (con, cursor):
            cursor.execute(query)
            con.commit()


class FilePageSearch(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_page = FilePage(**kwargs)

    def assemble_query(self, **kwargs):
        items = kwargs.get('search', '').split()
        page_size = kwargs.get('page_size', None)
        offset = kwargs.get('offset', None)
        for i in range(len(items)):
            items[i] = items[i].replace('_', ' ')
        search_groups = database_search.create_simple_search_groups(items)
        query = database_search.create_query_from_search_groups(search_groups)

        if page_size is not None:
            query += f" LIMIT {int(page_size)}"
        if offset is not None:
            query += f" OFFSET {int(offset)}"

        return query

    def get(self, **kwargs) -> List[Models.FilePage]:
        query = self.assemble_query(**kwargs)
        results = self._perform_select(query)
        ids = db_util.convert_tuple_to_list(results)
        return self.file_page.get(ids=ids)

    # Slightly optimized compared to separate get & count
    def get_and_count(self, **kwargs) -> (List[Models.FilePage], int):
        page_size = kwargs.get('page_size', None)
        offset = kwargs.get('offset', 0)
        del kwargs['page_size']
        del kwargs['offset']
        query = self.assemble_query(**kwargs)
        results = self._perform_select(query)
        ids = db_util.convert_tuple_to_list(results)
        count = len(ids)
        if page_size is None:
            ids = ids[offset:]
        else:
            ids = ids[offset:offset + page_size]
        file_pages = self.file_page.get(ids=ids)
        return file_pages, count

    def count(self, **kwargs) -> int:
        query = self.assemble_query(**kwargs)
        return self._perform_count(query)


class Tag(BaseClient):
    def assemble_query(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_names = create_entry_string(kwargs.get('names', []))
        allowed_pages = create_entry_string(kwargs.get('page_ids', []))
        allowed_classes = create_entry_string(kwargs.get('classes', []))
        query = f"SELECT tag.id, name, description, class, count(page_id) as count from tag" \
                f" left join tag_map on tag.id = tag_map.tag_id" \
                f" where tag.id in {allowed_ids} or name in {allowed_names} or class in {allowed_classes}" \
                f" or tag_map.page_id in {allowed_pages}" \
                f" group by tag.id"
        return query

    def get(self, **kwargs) -> List[Models.Tag]:
        query = self.assemble_query(**kwargs)
        rows = self._perform_select(query)
        mapping = ("id", "name", 'description', 'class', 'count')
        formatted = collection_util.tuple_to_dict(rows, mapping)
        results = []
        for row in formatted:
            results.append(Models.Tag(**row))
        return results

    def get_map(self, **kwargs) -> Dict[int, List[int]]:
        allowed_pages = create_entry_string(kwargs.get('page_ids', []))
        allowed_tags = create_entry_string(kwargs.get('tag_ids', []))
        query = f"SELECT page_id, tag_id from tag_map where page_id in {allowed_pages} or tag_id in {allowed_tags}"
        rows = self._perform_select(query)
        mapping = ("page_id", "tag_id")
        formatted = collection_util.tuple_to_dict(rows, mapping)
        result = {}
        for row in formatted:
            page = row['page_id']
            tag = row['tag_id']
            if page not in result:
                result[page] = []
            result[page].append(tag)
        return result

    def get_table(self, **kwargs) -> Dict[int, Models.Tag]:
        def get_key(tag: Models.Tag) -> int:
            return tag.id

        return collection_util.create_lookup(self.get(**kwargs), get_key)

    def count(self, **kwargs) -> Union[None, int]:
        return self._perform_count(self.assemble_query(**kwargs))

    def add_missing_tags(self, tags: List[str]):
        with Conwrapper(self.db_path) as (con, cursor):
            formatted_tag_list = create_value_string(tags)
            # Get tag_ids to set
            cursor.execute(f"INSERT OR IGNORE INTO tag (name) VALUES {formatted_tag_list}")
            con.commit()


class File(BaseClient):
    def assemble_query(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        query = f"SELECT id, path, extension from file" \
                f" where id in {allowed_ids}"
        return query

    def get(self, **kwargs):
        query = self.assemble_query(**kwargs)
        rows = self._perform_select(query)
        mapping = ("id", "path", 'extension')
        formatted = collection_util.tuple_to_dict(rows, mapping)
        results = []
        for row in formatted:
            results.append(Models.File(**row))
        return results

    def get_table(self, **kwargs) -> Dict[int, Models.File]:
        def get_key(file: Models.File) -> int:
            return file.file_id

        return collection_util.create_lookup(self.get(**kwargs), get_key)

    def count(self, **kwargs) -> Union[None, int]:
        return self._perform_count(self.assemble_query(**kwargs))
