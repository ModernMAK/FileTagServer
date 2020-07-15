import mimetypes
import re
from os.path import exists
from typing import Any, Dict, List, Optional, Tuple, Union

from litespeed.server import App
from litespeed.utils import Request


def render(request: Request, file: str, data: Dict[str, Any] = None, cache_age: int = 0,
           files: Optional[Union[List[str], str]] = None, status_override: int = None) -> Tuple[
    bytes, int, Dict[str, str]]:
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
    lines, status, headers = serve(file, cache_age, status_override=status_override)
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


def serve(file: str, cache_age: int = 0, headers: Optional[Dict[str, str]] = None, status_override: int = None) -> \
Tuple[bytes, int, Dict[str, str]]:
    """Send a file to the client.\n
    Allows for cache and header specification. Also allows to return a different _status code than 200\n
    :returns:Tuple[bytes, int, Dict[str, str]]"""
    file = file.replace('../',
                        '')  # prevent serving files outside of current / specified dir (prevents download of all system files)
    if headers is None:
        headers = {}
    if not exists(file):  # return 404 on file not exists
        return b'', 404, {}
    with open(file, 'rb') as _in:
        range = headers.get('RANGE')
        if range is None:
            lines = _in.read()
        else:
            try:
                import os
                # Video streaming requires MASSIVE speeds
                # according to a quich search for netflix, 1.5Mbps is recommended
                Bps = 1
                KBps = 1000 * Bps
                MBps = 1000 * KBps
                USHORT = 65535
                MAX_BYTES = MBps
                # trim off bytes=
                #unit=start-stop
                #start or stop can be omitted but not both
                range = range[6:]
                # split_on_len = range.split('/')
                # if len(split_on_len) > 1:
                #     requested_size = int(split_on_len[1])
                # else:
                requested_size = os.path.getsize(file)
                split_on_range = range.split('-')  # split_on_len[0].split('-')
                start = int(split_on_range[0])
                if len(split_on_range[1]) > 0:
                    stop = int(split_on_range[1])
                else:
                    stop = start + MAX_BYTES
                if stop > requested_size:
                    stop = requested_size
                read_len = stop - start
                _in.seek(start)
                lines = _in.read(read_len)
                headers['Content-Length'] = str(read_len)
                headers['Content-Range'] = f"bytes {start}-{stop-1}/{requested_size}"
                if start != requested_size:
                    status_override = 206
                else:
                    status_override = 200
            except Exception as e:
                print(e)
                lines = _in.read()

    if 'RANGE' in headers:
        del headers['RANGE']
    if 'Content-Type' not in headers:  # if content-type is not already specified then guess from mimetype
        ctype, encoding = mimetypes.guess_type(file)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        headers['Content-Type'] = ctype
    if cache_age > 0:
        headers['Cache-Control'] = f'max-age={cache_age}'
    elif not cache_age and file.split('.')[
        -1] != 'html' and not App.debug:  # if cache_age is not specified and not an html file and not debug then autoset cache_age to 1 hour
        headers['Cache-Control'] = 'max-age=3600'
    return lines, status_override or 200, headers
