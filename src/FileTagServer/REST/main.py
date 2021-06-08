from common import rest_api
import uvicorn
from FileTagServer.REST.file import tags_metadata as file_tagmetadata
from FileTagServer.REST.tag import tags_metadata as tags_tagmetadata

if __name__ == "__main__":
    tags_metadata = []
    parts = [file_tagmetadata, tags_tagmetadata]
    for part in parts:
        tags_metadata.extend(part)
    if len(tags_metadata) > 0:
        if not rest_api.openapi_tags:
            rest_api.openapi_tags = tags_metadata
        else:
            rest_api.openapi_tags.extend(tags_metadata)

    uvicorn.run(rest_api, host="localhost", port=8000)
