from typing import List

from litespeed import route, start_with_args, App

from src.FileTagServer.API.common import initialize_database
from src.rest.routes import files, files_tags, file_tags, files_search, tags, file, tag
from src.rest.common import url_join, url_protocol, serve_json
from src.rest.decorators import Endpoint
from src.rest.routes import tag_autocomplete, file_bytes

import src.rest.file as rest_file
import src.rest.tag as rest_tag


def finalize_routes(root=None, *, no_end_slash: bool = True, **route_kwargs):
    # A safety precaution
    rest_file.setup_routes()
    rest_tag.setup_routes()

    route_kwargs['no_end_slash'] = no_end_slash  # I do this because I personally prefer not having the trailing /
    INTEGER_REGEX = r"(\d+)"
    path_args = {
        'file_id': INTEGER_REGEX,
        'tag_id': INTEGER_REGEX,
        'root': root
    }
    endpoints: List[Endpoint] = [
        files, files_tags, files_search,
        file, file_tags, file_bytes,
        tags, tag, tag_autocomplete
    ]
    for ep in endpoints:
        ep.route(path_args, route_kwargs)


if __name__ == '__main__':
    initialize_database()
    finalize_routes()


    @route("/")
    def index(request):
        urls = {u.url: {'url': url_protocol("http", url_join("localhost", u.url)), 'methods': []} for u in App._urls}
        for u in App._urls:
            urls[u.url]['methods'].extend(u.methods)
        urls = list(urls.values())
        urls.sort(key=lambda d: d['url'])
        return serve_json(urls)


    start_with_args(port_default=80)
