from typing import Tuple, Optional, List

# SIMPLE BOOLEAN SEARCH
# Allows and/or/not operations
# assumes tags are do not have spaces

from pydantic import BaseModel

SEARCH_NOT = '-'
SEARCH_AND = '+'
SEARCH_OR = '~'
SEARCH_DELIMITER = " "


class SimpleSearchQuery(BaseModel):
    required: Optional[List[str]]
    include: Optional[List[str]]
    exclude: Optional[List[str]]



