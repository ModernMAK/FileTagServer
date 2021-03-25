from contextlib import contextmanager
from sqlite3 import Connection, Cursor, connect, Row
from typing import List, Tuple, Optional

from src import config


def __unexpected_field_error(name: str, expected: List[str]):
    if expected:
        return f"Unexpected field '{name}'; expected: {', '.join(expected)}"
    else:
        return f"Unexpected field '{name}'"


def __unallowed_field_error(name: str, allowed: List[str]):
    if allowed:
        return f"Unallowed field '{name}'; allowed: {', '.join(allowed)}"
    else:
        return f"Unallowed field '{name}'"


@contextmanager
def __connect(path=None, **kwargs) -> Tuple[Connection, Cursor]:
    path = path or config.db_path
    with connect(path, **kwargs) as conn:
        conn.execute("PRAGMA foreign_keys = 1")
        cursor = conn.cursor()
        cursor.row_factory = Row
        yield conn, cursor


def parse_sort_query(sort: str) -> Optional[List[Tuple[str, bool]]]:
    if sort is None:
        return None
    pairs = sort.split(",")
    results = []
    for pair in pairs:
        asc = True
        name = pair.strip()
        if pair[0] == "+":
            asc = True
            name = pair[1:].strip()
        elif pair[0] == "-":
            asc = False
            name = pair[1:].strip()
        results.append((name, asc))
    return results


def validate_sort_fields(sort: List[Tuple[str, bool]], allowed: List[str], expected: List[str]) -> Optional[List[str]]:
    if sort is None:
        return None
    errors = []
    for name, _ in sort:
        if name not in expected:
            errors.append(__unexpected_field_error(name, expected))
        elif name not in allowed:
            errors.append(__unallowed_field_error(name, allowed))

    if len(errors) > 0:
        return errors
    else:
        return None


def create_sort_sql(sort: List[Tuple[str, bool]] = None) -> Optional[str]:
    if sort is not None and len(sort) > 0:
        sort_str = []
        for field, asc in sort:
            sort_str.append(f"{field} {'ASC' if asc else 'DESC'}")
        return "ORDER BY " + ", ".join(sort_str)
    return None

