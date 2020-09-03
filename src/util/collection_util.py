from typing import List, Tuple, Any, Union, Dict, Set, Callable, Iterable


def list_tuple_to_list(values: List[Tuple[Any]]) -> List[Any]:
    return [v for value in values for v in value]


def tuple_to_dict(value: Union[None, Tuple, List[Tuple]], mapping: Union[Tuple, List]):
    if value is None:
        return {}
    if not isinstance(value, List):
        return {mapping[i]: value[i] for i in range(len(mapping))}
    else:
        return [{mapping[i]: row[i] for i in range(len(mapping))} for row in value]


def get_unique_values_on_key(rows: List[Dict[str, Any]], key: str) -> Set[Any]:
    return {row[key] for row in rows}


def get_unique_values(rows: Dict[Any, List[Any]]) -> Set[Any]:
    return {value for row in rows.values() for value in row}


def group_dicts_on_key(list_dict: List[Dict[Any, Any]], key: str) -> Dict[Any, List[Dict[Any, Any]]]:
    result = {}
    for d in list_dict:
        k = d[key]
        if k in result:
            result[k].append(d)
        else:
            result[k] = [d]
    return result


def create_lookup(data: List[Any], get_key: Callable[[Any], Any]) -> Dict[Any, Any]:
    return {get_key(value): value for value in data}


# List Of List,Value
def flatten(data: List[Union[Any, List[Any]]]) -> List[Any]:
    return [
        value for content in data for value in
        (
            flatten(*content) if isinstance(content, Iterable) and not isinstance(content, (str, bytearray))
            else (content,)
        )
    ]
