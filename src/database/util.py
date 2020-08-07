from typing import List, Dict, Any, Tuple, Union

from src.util import collection_util
from src.util.db_util import Conwrapper, to_sql_list, sanitize


def sql_in(name: str, values: List[Any], allow_empty: bool = False) -> Union[str, None]:
    if values is None or (not allow_empty and len(values) == 0):
        return None
    return f"{name} IN {to_sql_list(values)}"


def sql_in_like(name: str, values: List[Any], allow_empty: bool = False) -> Union[str, None]:
    if values is None or (not allow_empty and len(values) == 0):
        return None
    likes = []
    for value in values:
        likes.append(f"{name} IN {sanitize(value)}")
    return f"({sql_or_clauses(likes)})"


def sql_limit(limit: int) -> Union[str, None]:
    if limit is None:
        return None
    return f"LIMIT {int(limit)}"


def sql_offset(offset: int) -> Union[str, None]:
    if offset is None:
        return None
    return f"OFFSET {int(offset)}"


def remove_all_none(list: List[Any]) -> List[any]:
    return [item for item in list if item is not None]


def sql_combine_clauses(clauses: List[Union[str, None]], join='OR') -> Union[str, None]:
    if clauses is None:
        return None
    # remove nones
    clauses = remove_all_none(clauses)
    if all(clause is None for clause in clauses):
        return None

    if len(clauses) == 0:
        return None
    return f' {join} '.join(clauses)


def sql_or_clauses(clauses: List[Union[str, None]]) -> Union[str, None]:
    return sql_combine_clauses(clauses, 'OR')


def sql_and_clauses(clauses: List[Union[str, None]]) -> Union[str, None]:
    return sql_combine_clauses(clauses, 'AND')


def sql_order_by(name: str, ascending: bool = True) -> str:
    return f"ORDER BY {name} {'ASC' if ascending else 'DESC'}"


def sql_group_by(name: str) -> str:
    return f"GROUP BY {name}"


def sql_select_from(names: Union[Tuple[str], List[str], str], table: str, inner_query: bool = False) -> str:
    if not isinstance(names, str):
        names = ', '.join(names)
    if inner_query:
        table = f"({table})"
    return f"SELECT {names} FROM {table}"


def sql_where(clause: Union[str, None]) -> Union[str, None]:
    if clause is None:
        return None
    return f"WHERE {clause}"


def sql_assemble_query(query: str, constraints: Union[str, None] = None,
                       structure: Union[List[str], None] = None) -> str:
    constraints = sql_where(constraints)
    if structure:
        structure = remove_all_none(structure)
    if constraints is not None:
        query += " " + constraints
    if structure is not None and len(structure) > 0:
        query += " " + " ".join(structure)
    return query


def sql_create_table(table: str, values: List[str]) -> str:
    return f"CREATE TABLE IF NOT EXISTS {table}" \
           f"({', '.join(values)});"


def sql_assemble_modifiers(primary_key=False, auto_incriment=False) -> Union[str, None]:
    modifiers = []
    if primary_key:
        modifiers.append("PRIMARY KEY")
    if auto_incriment:
        modifiers.append("AUTOINCRIMENT")
    if len(modifiers) > 0:
        return " ".join(modifiers)
    return None


def sql_create_unique_value(name: str, values: List[str]):
    return f"CONSTRAINT {name} UNIQUE ({', '.join(values)})"


def sql_create_table_value(name: str, type: str, modifiers: Union[str, None] = None):
    if modifiers is not None:
        return f"{name} {type} {modifiers}"
    else:
        return f"{name} {type}"


class BaseClient:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path')

    def _fetch_all(self, query: str) -> List[Tuple]:
        with Conwrapper(self.db_path) as (con, cursor):
            cursor.execute(query)
            return cursor.fetchall()

    def _fetch_all_mapped(self, query: str, mapping: Tuple) -> List[Dict[str, Any]]:
        rows = self._fetch_all(query)
        return collection_util.tuple_to_dict(rows, mapping)

    def _fetch_all_lookup(self, query: str, mapping: Tuple, key: str) -> Dict[Any, Dict[str, Any]]:
        formatted = self._fetch_all_mapped(query, mapping)

        def get_key(d: Dict[str, Any]) -> Any:
            return d[key]

        return collection_util.create_lookup(formatted, get_key)

    def _count(self, query: str) -> int:
        with Conwrapper(self.db_path) as (con, cursor):
            cursor.execute(f"SELECT COUNT(*) FROM ({query})")
            count, = cursor.fetchone()  # COMMA IS IMPORTANT, untuples the fetch call
            return count

    def _execute(self, query: str) -> None:
        with Conwrapper(self.db_path) as (con, cursor):
            cursor.execute(query)
