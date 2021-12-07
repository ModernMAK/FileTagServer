from FileTagServer.REST.common import rest_api, initialize_routes
import uvicorn
from FileTagServer.REST.file import tags_metadata as file_tagmetadata
from FileTagServer.REST.tag import tags_metadata as tags_tagmetadata
from FileTagServer.REST.graph import dummy


def init():
    dummy()

    tags_metadata = []
    parts = [file_tagmetadata, tags_tagmetadata]
    for part in parts:
        tags_metadata.extend(part)
    if len(tags_metadata) > 0:
        if not rest_api.openapi_tags:
            rest_api.openapi_tags = tags_metadata
        else:
            rest_api.openapi_tags.extend(tags_metadata)


def run(**kwargs):
    init()
    initialize_routes()
    uvicorn.run(rest_api, **kwargs)


if __name__ == "__main__":
    run(host="localhost", port=8000)
