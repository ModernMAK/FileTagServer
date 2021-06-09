rest_route = "/rest"
files_route = f"{rest_route}/files"
files_tags_route = f"{files_route}/tags"
files_search_route = f"f{rest_route}/search"
file_route = f"{files_route}/{{file_id}}"
file_tags_route = f"{file_route}/tags"
file_bytes_route = f"{file_route}/bytes"
tags_route = f"{rest_route}/tags"
tags_search_route = f"f{rest_route}/search"
tag_route = f"{tags_route}/{{tag_id}}"
tag_files_route = f"{tag_route}/files"
tags_autocomplete = f"f{tags_route}/autocomplete"

graph_route = "/graphql"


def reformat(route: str, **kwargs):
    for k, v in kwargs.items():
        r = f"{{{k}}}"
        route = route.replace(r, str(v))
    return route
