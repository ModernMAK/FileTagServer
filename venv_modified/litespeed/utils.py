import json
import os
import re
import sys
from _pydecimal import Decimal
from datetime import date, datetime, time
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


class ExceptionReporter:
    """Organize and coordinate reporting on exceptions."""

    def __init__(self, request, exc_type, exc_value, tb):
        self.request = request
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb
        self.postmortem = None

    def get_traceback_data(self) -> Dict[str, Any]:
        """Return a dictionary containing traceback information.
        :returns:Dict[str, Any]"""
        frames = self.get_traceback_frames()
        for frame in frames:
            if 'vars' in frame:
                frame_vars = []
                for k, v in frame['vars']:
                    if isinstance(v, Request):
                        v = {k: v for k, v in v.items() if 'wsgi' not in k and k not in {'BODY'}}
                    try:
                        if isinstance(v, Dict):
                            if len(v) > 1000:
                                v = f'Length: {len(v)}'
                            else:
                                v = json.dumps(v, indent=4, sort_keys=True, default=json_serial).replace('\n',
                                                                                                         '<br>').replace(
                                    ' ', '&nbsp;')
                        elif isinstance(v, Iterable) and not isinstance(v, str):
                            if hasattr(v, '__len__') and len(v) > 1000:
                                v = f'Length: {len(v)}'
                            else:
                                v = json.dumps(v, indent=4, sort_keys=True, default=json_serial).replace('\n',
                                                                                                         '<br>').replace(
                                    ' ', '&nbsp;')
                        else:
                            v = repr(v).replace('<', '&lt;').replace('>', '&gt;')
                    except Exception as e:
                        v = f"Error in formatting: {e.__class__.__name__}: {e}".replace('<', '&lt;').replace('>',
                                                                                                             '&gt;')
                    frame_vars.append((k, repr(v) if not isinstance(v, str) else v))
                frame['vars'] = frame_vars
        unicode_hint = ''
        if self.exc_type and issubclass(self.exc_type, UnicodeError):
            start = getattr(self.exc_value, 'start', None)
            end = getattr(self.exc_value, 'end', None)
            if start is not None and end is not None:
                unicode_str = self.exc_value.args[1]
                unicode_hint = self.force_text(unicode_str[max(start - 5, 0):min(end + 5, len(unicode_str))], 'ascii',
                                               errors='replace')
        c = {
            'unicode_hint': unicode_hint,
            'frames': frames,
            'sys_executable': sys.executable,
            'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
            'sys_path': sys.path,
            'postmortem': self.postmortem,
        }
        # Check whether exception info is available
        if self.exc_type:
            c['exception_type'] = self.exc_type.__name__
        if self.exc_value:
            c['exception_value'] = str(self.exc_value)
        if frames:
            c['lastframe'] = frames[-1]
        return c

    def get_traceback_html(self) -> Tuple[bytes, int, Dict[str, str]]:
        """Return HTML version of debug 500 HTTP error page.
        :returns:Tuple[bytes, int, Dict[str, str]]"""
        from litespeed.helpers import render
        return render(self.request, f'{os.sep.join(__file__.split(os.sep)[:-1])}/html/500.html',
                      self.get_traceback_data(), status_override=500)

    @staticmethod
    def force_text(s, encoding: str = 'utf-8', strings_only: bool = False, errors: str = 'strict'):
        """Converts objects to str.
        If strings_only is True, don't convert (some) non-string-like objects."""
        if issubclass(type(s), str) or (
                strings_only and isinstance(s, (type(None), int, float, Decimal, datetime, date, time))):
            return s
        try:
            s = str(s, encoding, errors) if isinstance(s, bytes) else str(s)
        except UnicodeDecodeError as e:
            raise Exception(f'{e}. You passed in {s!r} ({type(s)})')
        return s

    @staticmethod
    def _get_lines_from_file(filename: str, lineno: int, context_lines: int, loader=None, module_name=None) -> Tuple[
        Optional[int], List[str], str, List[str]]:
        """Return context_lines before and after lineno from file.
        Return (pre_context_lineno, pre_context, context_line, post_context).
        :returns:Tuple[Optional[int], List[str], str, List[str]]"""
        source = None
        if hasattr(loader, 'get_source'):
            try:
                source = loader.get_source(module_name).splitlines()
            except ImportError:
                pass
        if source is None:
            try:
                with open(filename, 'rb') as fp:
                    source = fp.readlines()
            except (OSError, IOError):
                return None, [], '', []
        if isinstance(source[0],
                      bytes):  # If we just read the source from a file, or if the loader did not apply tokenize.detect_encoding to decode the source into a string, then we should do that ourselves.
            encoding = 'ascii'
            for line in source[:2]:
                match = re.search(br'coding[:=]\s*([-\w.]+)',
                                  line)  # File coding may be specified. Match pattern from PEP-263  (https://www.python.org/dev/peps/pep-0263/)
                if match:
                    encoding = match.group(1).decode('ascii')
                    break
            source = [str(_, encoding, 'replace') for _ in source]
        lower_bound = max(0, lineno - context_lines)
        return lower_bound, source[lower_bound:lineno], source[lineno], source[lineno + 1:lineno + context_lines]

    def get_traceback_frames(self) -> List[Dict[str, Any]]:
        """Returns a list of the traceback frames
        :returns:List[Dict[str, Any]]"""

        def explicit_or_implicit_cause(exc_value):
            """Return the cause of the exception. Returns the implicit if explicit does not exist."""
            return getattr(exc_value, '__cause__', None) or getattr(exc_value, '__context__', None)

        # Get the exception and all its causes
        exceptions = []
        exc_value = self.exc_value
        while exc_value:
            exceptions.append(exc_value)
            exc_value = explicit_or_implicit_cause(exc_value)
        if not exceptions:  # No exceptions were supplied to ExceptionReporter
            return []
        frames = []
        exc_value = exceptions.pop()
        tb = self.tb if not exceptions else exc_value.__traceback__  # In case there's just one exception, take the traceback from self.tb
        while tb is not None:
            if tb.tb_frame.f_locals.get(
                    '__traceback_hide__'):  # Support for __traceback_hide__ which is used by a few libraries to hide internal frames.
                tb = tb.tb_next
                continue
            filename = tb.tb_frame.f_code.co_filename
            lineno = tb.tb_lineno - 1
            pre_context_lineno, pre_context, context_line, post_context = self._get_lines_from_file(filename, lineno, 7,
                                                                                                    tb.tb_frame.f_globals.get(
                                                                                                        '__loader__'),
                                                                                                    tb.tb_frame.f_globals.get(
                                                                                                        '__name__') or '')
            if pre_context_lineno is None:
                pre_context_lineno = lineno
                context_line = '<source code not available>'
            frames.append({
                'exc_cause': explicit_or_implicit_cause(exc_value),
                'exc_cause_explicit': getattr(exc_value, '__cause__', True),
                'tb': tb,
                'filename': filename,
                'function': tb.tb_frame.f_code.co_name,
                'lineno': lineno + 1,
                'vars': tb.tb_frame.f_locals.items(),
                'id': id(tb),
                'pre_context': pre_context,
                'context_line': context_line,
                'post_context': post_context,
                'pre_context_lineno': pre_context_lineno + 1,
            })
            # If the traceback for current exception is consumed, try the other exception.
            if not tb.tb_next and exceptions:
                exc_value = exceptions.pop()
                tb = exc_value.__traceback__
            else:
                tb = tb.tb_next
        return frames


class HackedExceptionReporter(ExceptionReporter):
    def __init__(self, request, exc_type, exc_value, tb):
        super(HackedExceptionReporter, self).__init__(request, exc_type, exc_value, tb)

    def get_traceback_html(self) -> Tuple[bytes, int, Dict[str, str]]:
        """Return HTML version of debug 500 HTTP error page.
        :returns:Tuple[bytes, int, Dict[str, str]]"""
        from litespeed.helpers import render
        file_to_render = f'{os.sep.join(__file__.split(os.sep)[:-1])}/html/500.html'
        tb_data = self.get_traceback_data()
        tb_data['frames'].reverse()
        return render(self.request, file_to_render, tb_data, status_override=500)


class Request(dict):
    """Custom dict implementation to allow for cookies / sessions and accessing of dict keys as attributes"""

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return self[name]

    def __setattr__(self, key, value):
        self[key] = value

    def set_cookie(self, name, value, expires=None, max_age: Optional[int] = None, domain: Optional[str] = None,
                   path: Optional[str] = None, secure: Optional[bool] = None, http_only: Optional[bool] = None):
        if max_age is None:
            from litespeed.server import App
            max_age = App._cookie_age
        self['COOKIE'][name] = value
        self['COOKIE'][name].update({name: e for name, e in
                                     {'expires': expires, 'max-age': max_age, 'domain': domain, 'path': path,
                                      'secure': secure, 'httponly': http_only}.items() if e is not None})

    def set_session(self, name, value, domain: Optional[str] = None, path: Optional[str] = None,
                    secure: Optional[bool] = None, http_only: Optional[bool] = None):
        self.set_cookie(name, value, None, None, domain, path, secure, http_only)


def json_serial(obj: Any) -> Union[list, str, dict]:
    """JSON serializer for objects not serializable by default json code.
    :returns:Union[list, str, dict]"""
    try:
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if isinstance(obj, (set, tuple)):
            return list(obj)
        if isinstance(obj, bytes):
            return ''.join(map(chr, obj))
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        if hasattr(obj, '__str__'):
            return obj.__str__()
        if isinstance(obj, type(dict().items())):
            return dict(obj)
        raise TypeError(f'Type not serializable ({type(obj)})')
    except Exception as e:
        raise TypeError(f'Type not serializable ({type(obj)}) [{e.__str__()}]')
