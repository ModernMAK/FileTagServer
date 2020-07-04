from src.Routing.Pages import errors, file_page, page_utils


def initialize_module(**kwargs):
    errors.initialize_module(**kwargs)
    file_page.initialize_module(**kwargs)


# hardcoded for now
def add_routes():
    errors.add_routes()
    file_page.add_routes()
