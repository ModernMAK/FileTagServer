import configparser
from typing import Dict, Any


def configparser_as_dict(config):
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


def enforce_section(meta: Dict[str, Any], section: str) -> None:
    if section not in meta:
        meta[section] = {}


def write_id(meta: Dict[str, Any], id: int) -> None:
    enforce_section(meta, 'File')
    meta['File']['id'] = id


def write_hidden(meta: Dict[str, Any], hidden: bool) -> None:
    enforce_section(meta, 'File')
    meta['File']['ignore'] = hidden


def write_error_ignore(meta: Dict[str, Any], ignore: bool) -> None:
    enforce_section(meta, 'Error')
    meta['Error']['ignore'] = ignore


def pathed_get(d: Dict[str, Any], path: str, default: Any = None, delimiter: str = '.') -> Any:
    parts = path.split(delimiter)
    current = d
    for part in parts:
        if current is None or not isinstance(current, dict):
            return default
        current = current.get(part)

    if current is None:
        return default
    return current


def read_ini(path: str) -> Dict[str, Any]:
    parser = configparser.SafeConfigParser()
    with open(path, 'r') as file:
        parser.read_file(file)
        return configparser_as_dict(parser)


def write_ini(ini: Dict[str, Any], path: str):
    parser = configparser.SafeConfigParser()
    with open(path, 'w') as file:
        parser.read_dict(ini)
        parser.write(file)
