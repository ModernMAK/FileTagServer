from typing import List
from litespeed import start_with_args, route, App

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


@file.endpoint
def file_tags(*args, **kwargs):
    return 'tags'


@file.endpoint
def file_bytes(*args, **kwargs):
    return 'bytes'


# Endpoints can't be registered until after
def finalize_routes(root=None, *, no_end_slash: bool = True, **route_kwargs):
    route_kwargs['no_end_slash'] = no_end_slash  # I do this because I personally prefer not having the trailing /
    path_args = {
        'file_id': r'(\d)',
        'tag_id': r'(\d)',
        'root': root
    }
    endpoints: List[Endpoint] = [
        files, files_tags, file, file_tags, file_bytes,
    ]
    for ep in endpoints:
        ep.route(path_args, route_kwargs)


