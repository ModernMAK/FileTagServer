import sqlite3
from typing import List, Union, Tuple, Set


class Conwrapper():
    def __init__(self, db_path: str):
        try:
            self.con = sqlite3.connect(db_path)
            self.cursor = self.con.cursor()
        except sqlite3.OperationalError:
            print(f"db_path = '{db_path}'")
            raise
        
    def __enter__(self):
        return self.con, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()
        return exc_type is None


def sanitize(data: Union[object, List[object], Tuple[object]]) -> Union[str, List[str], Tuple[str]]:
    def sanatize_single(single_data: object) -> str:
        sanitized = str(single_data)
        sanitized = sanitized.replace("'", "''")
        if isinstance(single_data, str):
            sanitized = f"'{sanitized}'"  # SQL wraps strings in quotes
        return sanitized

    if isinstance(data, (list, tuple)):
        for i in range(len(data)):
            data[i] = sanatize_single(data[i])
        return data
    else:
        return sanatize_single(data)


def create_entry_string(data: Union[object, List[object]], skip_sanitize: bool = False) -> str:
    if isinstance(data, set):
        data = list(data)
    if isinstance(data, (list, tuple)):
        temp = []  # in the case of tuples, we cant assign back to data, so we use temp instead
        for i in range(len(data)):
            if skip_sanitize:
                temp.append(data[i])
            else:
                temp.append(sanitize(data[i]))
        return f"({','.join(temp)})"
    else:
        if skip_sanitize:
            return f"({data})"
        else:
            return f"({sanitize(data)})"


def create_value_string(values: Union[object, List[object], List[List[object]]]) -> str:
    result = []
    if isinstance(values, (list, tuple)):
        for i in range(len(values)):
            result.append(create_entry_string(values[i]))
    else:
        result = create_entry_string(result)
    return ','.join(result)


def convert_tuple_to_list(values: List[Tuple[object]]) -> List[object]:
    result = []
    for (value,) in values:
        result.append(value)
    return result
