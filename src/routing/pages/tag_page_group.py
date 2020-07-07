from src.routing.pages.page_group import PageGroup


class TagPageGroup(PageGroup):
    @classmethod
    def get_page(cls, id: str):
        return "/"