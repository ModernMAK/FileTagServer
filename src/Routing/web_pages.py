from src.Routing.Pages import errors, file_page, page_utils
from src.Routing.Pages.file_page_group import FilePageGroup


def initialize_module(**kwargs):
    FilePageGroup.initialize(**kwargs)
    errors.initialize_module(**kwargs)
    # file_page.Ini(**kwargs)


# hardcoded for now
def add_routes():
    errors.add_routes()
    FilePageGroup.add_routes()
