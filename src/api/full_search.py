from typing import Tuple, Optional, List

# FULL BOOLEAN SEARCH
# Allows grouping and literals
#
SEARCH_NOT = 'NOT'
SEARCH_AND = '+'
SEARCH_OR = '~'

SEARCH_GROUP_START = '('
SEARCH_GROUP_END = ')'
SEARCH_LITERAL = '"'

SEARCH_ESCAPE = "\\"


def _parse_group(query:str) -> List[str]:
    stack = []
    escaping = False
    for i, c in enumerate(query):
        if c == SEARCH_ESCAPE:
            escaping = True
            continue
        if escaping:
            escaping = False
            continue
        if c == SEARCH_GROUP_START:
            stack.append(i)
            continue
        if c == SEARCH_GROUP_END:
            start = stack.pop()
            yield query[start:i+1]
    if len(stack) > 0:
        raise ValueError


def parse(query: str) -> None:
    pass

if __name__ == "__main__":
    for g in _parse_group("()"):
        print(g)

    for g in _parse_group("(()"):
        print(g)




