from typing import List
from src.rest.common import url_join
from src.rest.decorators import Endpoint


@Endpoint
def rest(*args, root: str = None, **kwargs):
    return url_join(root or "/", 'rest')


@rest.endpoint
def files(*args, **kwargs):
    return f'files'


@files.endpoint
def file(*args, file_id=None, **kwargs):
    return file_id or '{file_id}'


@files.endpoint
def files_tags(*args, **kwargs):
    return 'tags'


@files.endpoint
def files_search(*args, **kwargs):
    return f"search"


@file.endpoint
def file_tags(*args, **kwargs):
    return 'tags'


@file.endpoint
def file_bytes(*args, **kwargs):
    return 'bytes'


@rest.endpoint
def tags(*args, **kwargs):
    return 'tags'


@tags.endpoint
def tag(*args, tag_id: int = None, **kwargs):
    return tag_id or "{tag_id}"


@tags.endpoint
def tag_autocomplete(*args, **kwargs):
    return 'autocomplete'
