import configparser
import enum
import io
import json
from typing import Dict, Any

try:
    import dicttoxml
except ImportError:
    class dicttoxml:
        def __getattribute__(self, item):
            raise NotImplementedError

        def __setattr__(self, key, value):
            raise NotImplementedError


class DictFormat(enum.Enum):
    json = 1
    xml = 2
    ini = 3


def configparser_as_dict(config: configparser.ConfigParser) -> Dict[Any, Any]:
    """
    https://stackoverflow.com/questions/1773793/convert-configparser-items-to-dictionary
    ~ James Kyle
    Converts a ConfigParser object into a dictionary.

    The resulting dictionary has sections as keys which point to a dict of the
    sections options as key => value pairs.
    """
    the_dict = {}
    for section in config.sections():
        the_dict[section] = {}
        for key, val in config.items(section):
            the_dict[section][key] = val
    return the_dict


def read_dict(file: str, format: DictFormat) -> Dict[Any, Any]:
    with open(file, 'r') as f:
        return str_to_dict(f.read(), format)


def write_dict(file: str, data: Dict[Any, Any], format: DictFormat) -> None:
    with open(file, 'w') as f:
        f.write(dict_to_str(data, format))


def dict_to_str(data: Dict[Any, Any], format: DictFormat) -> str:
    if format is DictFormat.json:
        return json.dumps(data)
    elif format is DictFormat.xml:
        return dicttoxml.dicttoxml(data)
    elif format is DictFormat.ini:
        config = configparser.ConfigParser()
        properly_formatted = all(isinstance(v, dict) for v in data.values())
        if not properly_formatted:
            config.read_dict({'ROOT': data})
        else:
            config.read_dict(data)
        with io.StringIO() as stream:
            config.write(stream)
            return stream.getvalue()
    else:
        raise NotImplementedError


def str_to_dict(data: str, format: DictFormat) -> Dict[Any, Any]:
    if format is DictFormat.json:
        return json.loads(data)
    elif format is DictFormat.xml:
        return dicttoxml.parseString(data)
    elif format is DictFormat.ini:
        config = configparser.ConfigParser()
        config.read_string(data)
        d = configparser_as_dict(config)
        temp_d = d.get('ROOT', None)
        if temp_d is not None:
            d = temp_d
        return d
    else:
        raise NotImplementedError


def nested_get(d: Dict[str, Any], path: str, default: Any = None, delimiter: str = '.') -> Any:
    parts = path.split(delimiter)
    current = d
    for part in parts:
        if current is None or not isinstance(current, dict):
            return default
        current = current.get(part)

    if current is None:
        return default
    return current
