from src.page_groups import static

db_path = "local.db" #pathing.Static.get_database(r"local.db")
template_path = static.html.resolve_path(r"templates")
host = "localhost"
port = "80"
protocol = "http"


def resolve_url(path:str) -> str:
    stripped_url = path.lstrip("/\\")
    delimiter = "//"
    if protocol.lower() == "file":  # Special case uses 3 '/'
        delimiter = "///"
    resolved_url = protocol + ":" + delimiter + host
    if len(stripped_url) > 0:
        resolved_url += "/" + stripped_url
    return resolved_url

