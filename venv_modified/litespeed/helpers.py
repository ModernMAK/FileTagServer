import mimetypes
import re
from os.path import exists
from secrets import token_hex
from typing import Any, Dict, List, Optional, Tuple, Union

from litespeed.server import App
from litespeed.utils import Request


def render(request: Request, file: str, data: Dict[str, Any] = None, cache_age: int = 0, files: Optional[Union[List[str], str]] = None, status_override: int = None) -> Tuple[bytes, int, Dict[str, str]]:
    """Send a file to the client, replacing ~~ controls to help with rendering blocks.\n
    Allows for ~~extends [file]~~, ~~includes [file]~~, and content blocks <~~[name]~~>[content]</~~[name]~~>.\n
    Extends will inject the blocks from this file to the one specified.\n
    Includes will paste the specified file in that spot.\n
    Contect blocks can be specified by ~~[name]~~ and used in files that extend <~~[name]~~>[content]</~~[name]~~>.\n
    Also allows for pure python by doing ~~[python code that returns / is a string]~~

    :returns:Tuple[bytes, int, Dict[str, str]]"""
    if data is None:
        data = {}
    if files is None:
        files = []
    lines, status, headers = serve(file, cache_age, status_override=status_override, range=request.HEADERS.get('RANGE'))
    if status in {200, status_override}:
        lines = lines.decode()
        if isinstance(files, str):
            files = [files]
        extends = re.search(r'~~extends ([\w\s./\\-]+)~~', lines.split('\n', 1)[0])
        if extends:
            return render(request, extends[1], data, cache_age, [file] + files)
        find = re.compile(r'<~~(\w+)~~>(.*?)</~~\1~~>', re.DOTALL)
        for file in files or []:
            if exists(file):
                with open(file, 'rt') as _in:
                    data.update({k: v for k, v in find.findall(_in.read())})
        for _ in range(2):
            for file in re.findall(r'~~includes ([\w\s./\\-]+)~~', lines):
                if exists(file):
                    with open(file) as _in:
                        lines = lines.replace(f'~~includes {file}~~', _in.read(), 1)
            for key, value in data.items():
                lines = lines.replace(f'~~{key}~~', str(value))
            for match in re.findall(r'(<?~~([^~]+)~~>?)', lines):
                if match[1][0] == '<':
                    continue
                try:
                    lines = lines.replace(match[0], str(eval(match[1], {'request': request, 'data': data})))
                except Exception as e:
                    if App.debug:
                        print(files, match[1], e.__repr__(), locals().keys(), sep='\t')
        lines = re.sub(r'<?/?~~[^~]+~~>?', '', lines).encode()
    return lines, status_override or status, headers


# Supports 206 Range requests
# DOES NOT SUPPORT 206 If-Range requests or Multipart Ranges
def serve(file: str, cache_age: int = 0, headers: Optional[Dict[str, str]] = None, status_override: int = None, range: str = None, max_bytes_per_request: int = None) -> Tuple[bytes, int, Dict[str, str]]:
    """Send a file to the client.\n
    Allows for cache and header specification. Also allows to return a different _status code than 200\n
    :returns:Tuple[bytes, int, Dict[str, str]]"""
    # prevent serving files outside of current / specified dir (prevents download of all system files)
    file = file.replace('../', '')
    if headers is None:
        headers = {}
    if not exists(file):  # return 404 on file not exists
        return b'', 404, {}
    if 'Content-Type' not in headers:  # if content-type is not already specified then guess from mimetype
        ctype, encoding = mimetypes.guess_type(file)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        headers['Content-Type'] = ctype
    with open(file, 'rb') as _in:
        if range is None:  # 200 request
            lines = _in.read()
        else:  # 206 Request
            unit, pairs = read_range(range)
            if unit != "bytes":
                return b'', 416, {}  # RANGE_NOT_SATISFIABLE
            import os
            content_size = os.path.getsize(file)
            ranges = []
            result = []
            for start, stop in pairs:  # get data for each range specified
                for old_start, old_stop in ranges:  # check range overlap and throw error if true
                    if old_start < start < old_stop or old_start < stop < old_stop:
                        return b'', 416, {}
                ranges.append((start, stop))
                if start is None:
                    start = content_size - stop
                    stop = content_size
                elif stop is None:
                    if max_bytes_per_request is None:  # TODO ask
                        stop = content_size
                    else:
                        stop = min(start + max_bytes_per_request, content_size)
                if start < 0 or start > stop or stop > content_size or (start is None and stop is None):  # validate range
                    return b'', 416, {}
                _in.seek(start)
                size = stop - start
                result.append((_in.read(size), f"{unit} {start}-{stop}/{content_size}"))
            if status_override is None:
                status_override = 206
            if len(result) > 1:
                boundary = token_hex(7)
                content = headers['Content-Type']
                headers['Content-Type'] = f'multipart/byteranges; boundary={boundary}'
                lines = '\n'.join(f'--{boundary}\nContent-Type: {content}\nContent-Range: {r[1]}\n\n{r[0]}' for r in result) + f'--{boundary}--'
    if cache_age > 0:
        headers['Cache-Control'] = f'max-age={cache_age}'
    elif not cache_age and file.split('.')[-1] != 'html' and not App.debug:  # if cache_age is not specified and not an html file and not debug then autoset cache_age to 1 hour
        headers['Cache-Control'] = 'max-age=3600'
    return lines, status_override or 200, headers


def read_range(range: str) -> Tuple[str, List[Tuple[Union[int, None], Union[int, None]]]]:
    """Parses a range string.\n
    Separates the string into the unit, and the range pairs.\n
    A None value in the pair range specifies that the value was not given, this is expected behaviour.
    :returns:Tuple[str,List[Tuple[Union[int,None],Union[int,None]]]]"""
    format, split_on_pairs = range.split('=', 1)
    split_on_pairs = split_on_pairs.split(',')
    pairs = []
    for pair_str in split_on_pairs:
        split_on_range = pair_str.split('-', 1)
        start = int(split_on_range[0]) if len(split_on_range[0]) > 0 else None
        stop = int(split_on_range[1]) if len(split_on_range[1]) > 0 else None
        pairs.append((start, stop))
    return format, pairs