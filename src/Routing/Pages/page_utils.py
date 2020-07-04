from math import ceil
from typing import Dict, Tuple, Any, Callable


def escape_js_string(input: str) -> str:
    input = input.replace('/', '//')
    input = input.replace("'", '/')
    input = input.replace('"', '/"')
    return input


def reformat_serve(renderer, serve_content: Tuple[bytes, int, Dict[str, str]], context: Dict[str, Any] = None) -> Tuple[
    bytes, int, Dict[str, str]]:
    if context is None:
        context = {}

    content, status, header = serve_content
    fixed_content = renderer.render(content, context)
    return fixed_content, status, header


def get_pagination_symbols(items: int, page_size: int, current_page: int, get_page_path: Callable[[int], str],
                           range_size: int = 5):
    pages = int(ceil(items / page_size))
    current_page = int(current_page)

    def get_pairs():
        # Symbol, Link, Current
        symbols = []
        # Constants for styling
        CURRENT = 'active'
        DISABLED = 'disabled'

        if current_page > 1:
            symbols.append(('<<', 1, None))
        else:
            symbols.append(('<<', None, DISABLED))

        if current_page > 1:
            symbols.append(('<', current_page - 1, None))
        else:
            symbols.append(('<', None, DISABLED))

        if current_page > range_size + 1:
            symbols.append(('...', None, DISABLED))

        for i in range(current_page - range_size, current_page + range_size + 1):
            if 1 <= i <= pages:
                if i == current_page:
                    symbols.append((i, None, CURRENT))
                else:
                    symbols.append((i, i, None))

        if current_page < pages - range_size - 1:
            symbols.append(('...', None, DISABLED))

        if current_page < pages:
            symbols.append(('>', current_page + 1, None))
        else:
            symbols.append(('>', None, DISABLED))

        if current_page < pages:
            symbols.append(('>>', pages, None))
        else:
            symbols.append(('>>', None, DISABLED))
        return symbols

    context = []
    pairs = get_pairs()
    for pair in pairs:
        symbol, page, status = pair
        if page is None:
            local_context = {'RAW': {'SYMBOL': symbol, 'STATUS': status}}
        else:
            local_context = {'PAGE': {'PATH': get_page_path(page), 'SYMBOL': symbol, 'STATUS': status}}
        context.append(local_context)

    return {'PAGES': context}
