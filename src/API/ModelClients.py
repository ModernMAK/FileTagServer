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


def list_dict_to_dict_list_dict(list_dict: List[Dict[Any, Any]], key: str) -> Dict[Any, List[Dict[Any, Any]]]:
    result = {}
    for d in list_dict:
        k = d[key]
        if k in result:
            result[k].append(d)
        else:
            result[k] = [d]
    return result


def create_mipmap_table(mipmaps: List[Models.ImageMipmap]) -> Dict[int, Models.ImageMipmap]:
    d = {}
    for mipmap in mipmaps:
        d[mipmap.mipmap_id] = mipmap
    return d


def create_tag_table(tags: List[Models.Tag]) -> Dict[int, Models.Tag]:
    d = {}
    for tag in tags:
        d[tag.id] = tag
    return d


class BaseClient:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path')

    def _perform_select(self, select_query: str):
        try:
            with Conwrapper(self.db_path) as (con, cursor):
                cursor.execute(select_query)
                return cursor.fetchall()
        except sqlite3.DatabaseError:
            return None


class ImagePost(BaseClient):

    def get(self, **kwargs) -> List[Models.ImagePost]:
        # GATHER ARGS
        page_size = kwargs.get('page_size', None)
        offset = kwargs.get('offset', None)
        requested_ids = kwargs.get('ids', None)

        # ASSEMBLE QUERY
        query = f"SELECT image_post.id, image_post.post_id, post.name, post.description, image_post.mipmap_id from image_post" \
                f" inner join post on post.id = image_post.post_id"

        if any(v is not None for v in [requested_ids]):
            query += " where"
            append_or = False
            if requested_ids is not None:
                if append_or:
                    query += " or"
                query += f" image_post.id in {create_entry_string(requested_ids)}"
                append_or = True

        if page_size is not None:
            query += f" LIMIT {int(page_size)}"
        if offset is not None:
            query += f" OFFSET {int(offset)}"

        # PERFORM QUERY
        rows = self._perform_select(query)

        # FORMAT RESULTS
        mapping = ("id", "post_id", "name", "description", "mipmap_id")
        formatted = tuple_to_dict(rows, mapping)

        # GATHER ADDITIONAL TABLES ~ MIP MAPS
        unique_mipmaps = get_unique_helper(formatted, 'mipmap_id')
        mipmap_client = ImageMipMap(db_path=self.db_path)
        mipmap_table = create_mipmap_table(mipmap_client.get(ids=unique_mipmaps))

        # GATHER ADDITIONAL TABLES ~ TAGS
        unique_posts = get_unique_helper(formatted, 'post_id')
        tag_client = Tag(db_path=self.db_path)
        formatted_tag_map = tag_client.get_map(post_ids=unique_posts)
        unique_tags = formatted_tag_map.keys()
        tag_table = create_tag_table(tag_client.get(ids=unique_tags))

        # RETURN ASSEMBLED MODELS
        results = []
        for row in formatted:
            post = Models.ImagePost(**row)
            post.mipmap = mipmap_table[row['mipmap_id']]
            post.tags = []

            if post.post_id in formatted_tag_map:
                for tag_id in formatted_tag_map[post.post_id]:
                    post.tags.append(tag_table[tag_id])
            results.append(post)
        return results


class ImageMipMap(BaseClient):
    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        query = f"SELECT image_mipmap.id, image_mip.id, image_mip.name, image_mip.scale, image_file.width, image_file.height, file.real_path, file.virtual_path, file.id, file.extension" \
                f" from image_mipmap" \
                f" inner join image_mip on image_mip.map_id = image_mipmap.id" \
                f" inner join image_file on image_mip.image_id = image_file.id" \
                f" inner join file on image_file.file_id = file.id" \
                f" where image_mipmap.id in {allowed_ids}"

        rows = self._perform_select(query)
        mapping = ("id", "mip_id", "name", 'scale', 'width', 'height', 'path', 'v_path', 'file_id', 'extension')
        formatted = tuple_to_dict(rows, mapping)
        mipmap_lookup = list_dict_to_dict_list_dict(formatted, "id")
        results = []
        for id in mipmap_lookup:
            mips_data = mipmap_lookup[id]
            model = Models.ImageMipmap(id=id)
            model.mips = []
            for mip_data in mips_data:
                mip_data['id'] = mip_data['mip_id']
                mip = Models.ImageMip(**mip_data)
                model.mips.append(mip)
            results.append(model)
        return results


class Tag(BaseClient):
    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        allowed_names = create_entry_string(kwargs.get('names', []))
        allowed_posts = create_entry_string(kwargs.get('post_ids', []))
        allowed_classes = create_entry_string(kwargs.get('classes', []))
        query = f"SELECT tag.id, name, description, class, count(post_id) as count from tag" \
                f" left join tag_map on tag.id = tag_map.tag_id" \
                f" where tag.id in {allowed_ids} or name in {allowed_names} or class in {allowed_classes}" \
                f" or tag_map.post_id in {allowed_posts}" \
                f" group by tag.id"
        rows = self._perform_select(query)
        mapping = ("id", "name", 'description', 'class', 'count')
        formatted = tuple_to_dict(rows, mapping)
        results = []
        for row in formatted:
            results.append(Models.Tag(**row))
        return results

    def get_map(self, **kwargs) -> Dict[int, List[int]]:
        allowed_posts = create_entry_string(kwargs.get('post_ids', []))
        query = f"SELECT tag_map.post_id, tag_map.id from tag_map where tag_map.post_id in {allowed_posts}"
        rows = self._perform_select(query)
        mapping = ("post_id", "tag_id")
        formatted = tuple_to_dict(rows, mapping)
        result = {}
        for row in formatted:
            post = row['post_id']
            tag = row['tag_id']
            if post not in result:
                result[post] = []
            result[post].append(tag)
        return result


class File(BaseClient):
    def get(self, **kwargs):
        allowed_ids = create_entry_string(kwargs.get('ids', []))
        query = f"SELECT id, real_path, extension, virtual_path from file" \
                f" where id in {allowed_ids}"

        rows = self._perform_select(query)
        mapping = ("id", "real_path", 'extension', 'virtual_path')
        return tuple_to_dict(rows, mapping)
