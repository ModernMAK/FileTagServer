from math import ceil
from typing import Callable


class PaginationUtil:
    @staticmethod
    def is_page_offset_valid(offset: int, size: int, count: int) -> bool:
        return count - (offset + size) > 0

    @staticmethod
    def is_page_valid(page: int, size: int, count: int) -> bool:
        return PaginationUtil.is_page_offset_valid(page * size, size, count)

    @staticmethod
    def get_page_count(size: int, count: int) -> int:
        return ceil(count / size)

    # Returns a dictionary with information regarding

    # url generator should expect urls in 0-notation, and output them in 1-notation
    @staticmethod
    def get_pagination(current_page: int, total_pages: int, page_neighbors: int, url_generator: Callable[[int], str]):
        # Pages - > Link/Plain -> [url, status, text]
        JUMP_FIRST = "&laquo;"
        JUMP_PREV = "&lsaquo;"
        SKIP_AREA = "&hellip;"
        JUMP_NEXT = "&rsaquo;"
        JUMP_LAST = "&raquo;"

        parts = []

        def create_link(text, url, disable: bool = False, **kwargs):
            part = {"url": url, "text": text}
            if disable:
                part['status'] = "disabled"
            parts.append({"link": part})

        def create_plain(text, disable: bool = False, **kwargs):
            part = {"text": text}
            if disable:
                part['status'] = "disabled"
            parts.append({"plain": part})

        def create_optional(text, url, use_link: bool, **kwargs):
            kwargs['text'] = text
            kwargs['url'] = url

            if use_link:
                create_link(**kwargs)
            else:
                create_plain(**kwargs)

        # First Icon
        create_optional(JUMP_FIRST, url_generator(0), use_link=(current_page != 0))
        create_optional(JUMP_PREV, url_generator(current_page - 1), use_link=(current_page > 0))
        # current - neighbors > 0 garuntees we hide page 0
        if current_page - page_neighbors > 0:
            create_plain(SKIP_AREA)

        min_page = max(0, current_page - page_neighbors)
        max_page = min(total_pages, current_page + page_neighbors)

        for i in range(min_page, max_page + 1):
            create_optional(i + 1, url_generator(i), use_link=i != current_page)

        if current_page + page_neighbors < total_pages - 1:
            create_plain(SKIP_AREA)
        create_optional(JUMP_NEXT, url_generator(current_page + 1), use_link=(current_page < total_pages - 1))
        create_optional(JUMP_LAST, url_generator(total_pages - 1), use_link=(current_page != total_pages - 1))

        return {"pages": parts}

# {{#pagination}}
#     <nav class="row mx-auto w-50 justify-content-center">
#         <ul class="pagination">
#             {{#pages}}
#                 {{#link}}
#                     <li class="page-item {{status}}">
#                         <a href="{{url}}" class="page-link">{{text}}</a>
#                     </li>
#                 {{/link}}
#                 {{#plain}}
#                     <li class="page-item {{status}}"><span class="page-link">{{symbol}}</span></li>
#                 {{/plain}}
#             {{/pages}}
#         </ul>
#     </nav>
# {{/pagination}}
# {{^pagination}}
#     <!-- If you are reading this, then somebody goofed the pagination script -->
# {{/pagination}}
