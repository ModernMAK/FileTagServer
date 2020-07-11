import json
import re
import socket
import struct
import sys
from base64 import b64encode
from collections import namedtuple
from _collections_abc import dict_keys
from datetime import datetime
from functools import partial
from gzip import GzipFile
from hashlib import sha1
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from socketserver import ThreadingTCPServer
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union
from urllib.parse import parse_qs, unquote_plus
from wsgiref.handlers import SimpleHandler

from litespeed.mail import Mail
from litespeed.utils import ExceptionReporter, json_serial, Request


class WebServer(ThreadingTCPServer):
    request_queue_size = 500
    allow_reuse_address = True
    application = None
    base_environ = Request()
    daemon_threads = True
    clients, handlers = {}, {}
    id_counter = 0
    websocket_handlers = {'new': [], 'message': [], 'left': []}

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate: bool = True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

    def server_bind(self):
        """Override server_bind to store the server name."""
        super().server_bind()
        self.setup_env(self.server_address[1])

    @classmethod
    def attach_websocket_handler(cls, type: str, function: Callable[[dict, ThreadingTCPServer, Optional[str]], None]):
        if type not in {'new', 'message', 'left'}:
            raise ValueError
        cls.websocket_handlers[type].append(function)

    @classmethod
    def setup_env(cls, port: int):
        if not cls.base_environ:
            cls.base_environ = Request({'SERVER_NAME': socket.gethostname(), 'GATEWAY_INTERFACE': 'CGI/1.1', 'SERVER_PORT': str(port), 'REMOTE_HOST': '', 'CONTENT_LENGTH': '', 'SCRIPT_NAME': ''})

    def message_received(self, handler, msg):
        self.handle(self.handlers[id(handler)], 'message', msg)

    def new_client(self, handler, env):
        self.id_counter += 1
        client = {
            'id': self.id_counter,
            'handler': handler,
            'request': env,
            'handler_id': id(handler)
        }
        self.handlers[client['handler_id']] = self.clients[client['id']] = client
        self.handle(client, 'new')

    def client_left(self, handler):
        try:
            client = self.handlers[id(handler)]
            self.handle(client, 'left')
            del self.clients[client['id']]
            del self.handlers[client['handler_id']]
        except KeyError:
            pass
        for client in list(self.clients.values()):
            if client['handler'].connection._closed:
                del self.clients[client['id']]
                del self.handlers[client['handler_id']]
        for client in list(self.handlers.values()):
            if client['handler'].connection._closed:
                del self.clients[client['id']]
                del self.handlers[client['handler_id']]

    def handle(self, client, type: str, msg=None):
        for f in self.websocket_handlers[type]:
            f(client, self, *([msg] if msg else []))

    @staticmethod
    def send_message(client, msg):
        client['handler'].send_message(msg)

    @staticmethod
    def send_json(client, obj):
        client['handler'].send_json(obj)

    def send_message_all(self, msg):
        for client in self.clients.values():
            client['handler'].send_message(msg)

    def send_json_all(self, obj):
        for client in self.clients.values():
            client['handler'].send_json(obj)

    def serve(self):
        print(f'Server Started on {self.server_address}')
        try:
            self.serve_forever(.1)
        except KeyboardInterrupt:
            self.shutdown()


class App:
    """Handles request from client"""
    __route_cache = {}
    _urls = {}
    _status = {s.value: f'{s.value} {s.phrase}' for s in HTTPStatus}
    debug = False
    _cookie_age = 3600
    _cors_origins_allow = set()
    _cors_methods_allow = set()
    _admins = []
    error_routes = {}

    def __init__(self):
        if 500 not in self.error_routes:
            self.error_routes[500] = self._500

    def _500(self, request: Request, *args, **kwargs):
        e = '', 500
        if self._admins or self.debug:
            e = ExceptionReporter(request, *sys.exc_info()).get_traceback_html()
        if self._admins and not self.debug:
            Mail(f'Internal Server Error: {request["PATH_INFO"]}', '\n'.join(str(e) for e in sys.exc_info()), self._admins, html=e[0].decode()).embed().send()
            e = '', 500
        return e

    def __call__(self, env: dict, start_response: Callable):
        path = env['PATH_INFO']
        f = self._handle_route_cache(path)
        env = Request(env)
        headers = {}
        cookie = set(env['COOKIE'].output().replace('\r', '').split('\n'))
        called = False
        try:
            if isinstance(f, bool):
                result = self.error_routes.get(404, (lambda e: (b'', 404, {'Content-Type': 'text/public'})))(env)
            if path[-1:] != '/' and 'result' not in locals() and not f[0].no_end_slash:  # auto rediects to url that ends in / if no_end_slash is False
                result = self.error_routes.get(307, (lambda e, *a, **k: (b'', 307, {'Location': f'{path}/'})))(env, *f[1], **f[2])
            if 'result' not in locals():
                r = self._handle_cors(f, headers, env)
                if ('*' not in f[0].methods and env['REQUEST_METHOD'].lower() not in f[0].methods) or not r:  # checks for allowed methods
                    result = self.error_routes.get(405, (lambda e, *a, **k: (b'', 405, {'Content-Type': 'text/public'})))(env, *f[1], **f[2])
                else:
                    result = f[0](env, *f[1], **f[2])
                    called = True
        except Exception:
            result = self.error_routes[500](env, *f[1], **f[2])
        r = self._handle_result(result, headers, cookie, env)
        status = int(r[1].split()[0])
        if called and status in self.error_routes and status not in f[0].disable_default_errors:
            r = self._handle_result(self.error_routes[status](env, *f[1], **f[2]), headers, cookie, env)
        start_response(*r[1:])
        return r[0]

    @classmethod
    def register_error_page(cls, function: Callable = None, code: int = None):
        assert code is not None

        def _wrapped(function: Callable):
            cls.error_routes[code] = function
            return function

        if function:
            return _wrapped(function)
        return _wrapped

    @staticmethod
    def compress_string(s: str) -> bytes:
        """Compresses a string using gzip"""
        zbuf = BytesIO()
        with GzipFile(mode='wb', compresslevel=6, fileobj=zbuf, mtime=0) as zfile:
            zfile.write(s)
        return zbuf.getvalue()

    def _handle_cors(self, f: Callable, headers: dict, env: dict) -> bool:
        def _check_cors() -> bool:
            cors = f[0].cors or self._cors_origins_allow  # checks for cors allowed domains using route override of global
            if cors:
                if '*' in cors:
                    headers['Access-Control-Allow-Origin'] = '*'
                elif env.get('ORIGIN', '').lower() in cors:
                    headers['Access-Control-Allow-Origin'] = env['ORIGIN']
                else:
                    return False
            return True

        methods = f[0].cors_methods or self._cors_methods_allow
        if methods:  # checks for cors allowed methods using route override of global
            if '*' in methods:
                headers['Access-Control-Allow-Method'] = '*'
                return True
            elif env['REQUEST_METHOD'].lower() in methods:
                headers['Access-Control-Allow-Method'] = env['REQUEST_METHOD']
                return _check_cors()
            else:
                return False
        else:
            return _check_cors()

    @classmethod
    def add_websocket(cls, function: Callable[[dict, WebServer, Optional[str]], None] = None, type: str = None):
        if type not in {'new', 'message', 'left'}:
            raise ValueError

        def _wrapped(function: Callable[[dict, WebServer, Optional[str]], None]):
            WebServer.websocket_handlers[type].append(function)
            return function

        if function:
            return _wrapped(function)
        return _wrapped

    def _handle_result(self, result, headers: dict, cookie: set, env: Request) -> Tuple[List[bytes], str, List[tuple]]:
        body = ''
        status = '200 OK'

        def _process_headers(request_headers):
            if isinstance(request_headers, dict):
                headers.update(request_headers)
            elif isinstance(request_headers, tuple):
                headers.update(dict(request_headers))
            elif isinstance(request_headers, list) and isinstance(request_headers[0], tuple):
                headers.update(dict(result))

        def _handle_status(_status):
            nonlocal status
            if not _status:
                status = '200 OK'
            else:
                status = self._status[_status] if isinstance(_status, int) else _status if not isinstance(_status, HTTPStatus) else f'{_status.value} {_status.phrase}'

        def _handle_compression():
            nonlocal body
            body_len = len(body[0])
            if 'gzip' in env.get('ACCEPT_ENCODING', '').lower() and body_len > 200 and 'image' not in headers.get('Content-Type', '').lower():
                compressed_body = self.compress_string(body[0])
                compressed_len = len(compressed_body)
                if compressed_len < body_len:
                    body = [compressed_body]
                headers['Content-Length'] = str(compressed_len)
                headers['Content-Encoding'] = 'gzip'

        if result:  # if result is not None parse for body, _status, headers
            if isinstance(result, (tuple, type(namedtuple), list)):
                l_result = len(result)
                body = result[0] if l_result <= 3 else result
                if 3 >= l_result > 1:
                    _handle_status(result[1])
                    if l_result > 2 and result[2]:
                        _process_headers(result[2])
                if callable(body):
                    body = body()
                elif isinstance(body, dict):
                    body = json.dumps(body, default=json_serial).encode()
                    headers['Content-Type'] = 'application/json; charset=utf-8'
                elif isinstance(body, dict_keys):
                    body = list(body)
            elif isinstance(result, dict):
                if 'body' in result:
                    body = result['body']
                    if callable(body):
                        body = body()
                _handle_status(result.get('_status'))
                if 'headers' in result:
                    _process_headers(result['headers'])
                if not (body or status != '200 OK'):
                    body = json.dumps(result, default=json_serial).encode()
                    headers['Content-Type'] = 'application/json; charset=utf-8'
            elif isinstance(result, (str, bytes)):
                body = result
        else:  # set 501 status code when falsy result
            status = '501 Not Implemented'
        if 'Content-Type' not in headers:  # add default html header if none passed
            headers['Content-Type'] = 'text/html; charset=utf-8'
        body = body if isinstance(body, list) and ((body and isinstance(body[0], bytes)) or not body) else [b.encode() for b in body] if isinstance(body, list) and ((body and isinstance(body[0], str)) or not body) else [body] if isinstance(body, bytes) else [body.encode()] if isinstance(body, str) else [str(body).encode()] if isinstance(body, int) else body
        if body:
            _handle_compression()
        return body, status, [(k, v) for k, v in headers.items()] + [('Set-Cookie', c[12:]) for c in env.COOKIE.output().replace('\r', '').split('\n') if c not in cookie]

    def _handle_route_cache(self, path: str) -> Union[bool, Callable]:
        if path not in self.__route_cache:  # finds url from urls and adds to ROUTE_CACHE to prevent future lookups
            for _, url in self._urls.items():
                tmp = path + ('/' if not url.no_end_slash and path[-1] != '/' and url.re.pattern[-1] == '/' else '')
                m = url.re.fullmatch(tmp[1:]) if tmp and tmp[0] == '/' and url.re.pattern[0] != '/' else url.re.fullmatch(tmp)
                if m:
                    groups = m.groups()
                    for key, value in m.groupdict().items():
                        if value in groups:
                            groups = (g for g in groups if g != value)
                    self.__route_cache[path] = (url, groups, m.groupdict())
                    url.cache.append(path)
                    break
            else:
                return False
        return self.__route_cache[path]

    @classmethod
    def route(cls, url: Optional[str] = None, methods: Union[Iterable, str] = '*', function: Callable = None, cors: Optional[Union[Iterable, str]] = None, cors_methods: Optional[Union[Iterable, str]] = None, no_end_slash: bool = False, disable_default_errors: Optional[Iterable[int]] = None):
        """Handles adding function to urls"""

        def decorated(func) -> partial:
            nonlocal url
            if url is None:
                url = (func.__module__.replace('.', '/') + '/').replace('__main__/', '') + (func.__name__ + '/').replace('index/', '')
            if not url or (url[-1] != '/' and '.' not in url[-5:] and not no_end_slash):
                url = (url or '') + '/'
            if url not in cls._urls:
                func.no_end_slash = no_end_slash
                func.url = url
                func.re = re.compile(url)
                func.methods = {m.lower() for m in methods} if isinstance(methods, (list, set, dict, tuple)) else set(methods.lower().split(','))
                func.cors = None if not cors else {c.lower() for c in cors} if isinstance(cors, (list, set, dict, tuple)) else {c for c in cors.lower().strip().split(',') if c}
                func.cors_methods = None if not cors_methods else {c.lower() for c in cors_methods} if isinstance(cors_methods, (list, set, dict, tuple)) else {c for c in cors_methods.lower().strip().split(',') if c}
                func.cache = []
                func.disable_default_errors = set(disable_default_errors) if disable_default_errors else set()
                cls._urls[url] = func
            return partial(func)

        if function:
            return decorated(function)
        return decorated

    @classmethod
    def clear_route_cache(cls, path=None):
        if path:
            del cls.__route_cache[path]
        else:
            cls.__route_cache.clear()


class RequestHandler(BaseHTTPRequestHandler):
    """"""
    """websocket packet
    +-+-+-+-+-------+-+-------------+-------------------------------+
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-------+-+-------------+-------------------------------+
    |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
    |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
    |N|V|V|V|       |S|             |   (if payload len==126/127)   |
    | |1|2|3|       |K|             |                               |
    +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
    |     Extended payload length continued, if payload len == 127  |
    + - - - - - - - - - - - - - - - +-------------------------------+
    |                     Payload Data continued ...                |
    +---------------------------------------------------------------+
    """

    def __init__(self, request, client_address, server):
        self.keep_alive = True
        self.handshake_done = False
        self.valid_client = False
        super().__init__(request, client_address, server)
        self.raw_requestline, self.requestline, self.request_version, self.command = '', '', '', ''

    @staticmethod
    def _get_boundary_enclosed(boundary: List[str], env: Request):
        boundary = boundary[0] + '--'
        line, content, name, filename = '', '', '', ''
        dashes = re.compile(r'-*')
        re_name = re.compile(r'name="(.*?)"')
        re_filename = re.compile(r'filename="(.*?)"')
        file = None
        skip_first = True
        body = env['BODY'].split(b'\n')
        i = 0
        while not line or isinstance(line, bytes) or dashes.sub('', line, 1) != boundary:
            line = body[i] + (b'\n' if i < len(body) else b'')
            try:
                decoded = line.decode().replace('\r', '').replace('\n', '')
                if decoded:
                    if dashes.sub('', decoded, 1) in {boundary[:-2], boundary}:
                        name, filename, content = '', '', ''
                        skip_first = True
                        if file:
                            file.seek(0)
                    if not content:
                        if not name:
                            name = (re_name.findall(decoded) or [''])[0]
                        if not filename:
                            filename = re_filename.findall(decoded)
                            if filename:
                                filename = filename[0]
                                file = BytesIO()
                        if decoded.startswith('Content-Type'):
                            content = decoded.split(' ')[-1]
            except UnicodeDecodeError:
                decoded = ''
            if content and ((decoded and not decoded.startswith('Content-Type')) or not decoded):
                if filename not in env['FILES'].get(name, {}):
                    if name not in env['FILES']:
                        env['FILES'][name] = {filename: file}
                    else:
                        env['FILES'][name][filename] = file
                if not skip_first:
                    file.write(line)
                else:
                    skip_first = False
            elif name and ((decoded and not re_name.findall(decoded)) or decoded != line) and not filename:
                env[env['REQUEST_METHOD']][name] = decoded if decoded and dashes.sub('', decoded, 1) != boundary else line
                name = ''
            if not content:
                line = decoded
            i += 1

    @staticmethod
    def _parse_qs(qs) -> dict:
        return {k: v if len(v) > 1 else v[0] for k, v in parse_qs(qs).items()}

    def get_environ(self) -> Request:
        """Read headers / body and generate Request object.
        :returns:Request"""
        env = Request({'SERVER_PROTOCOL': self.request_version, 'SERVER_SOFTWARE': self.server_version, 'REQUEST_METHOD': self.command.upper(), 'BODY': b'', 'GET': {}, 'POST': {}, 'PATCH': {}, 'PUT': {}, 'OPTIONS': {}, 'DELETE': {}, 'FILES': {}, 'COOKIE': SimpleCookie(self.headers.get('COOKIE')), 'HEADERS': dict(self.headers), 'REMOTE_ADDR': self.client_address[0], 'CONTENT_TYPE': self.headers.get_content_type(), 'HOST': self.headers['HOST']})
        env['HEADERS'] = {k.upper().strip(): v for k, v in env['HEADERS'].items()}
        path, env['QUERY_STRING'] = self.path.split('?', 1) if '?' in self.path else (self.path, '')
        env['PATH_INFO'] = unquote_plus(path, 'iso-8859-1')
        host = env['HEADERS'].get('X-REAL-IP') or env['HEADERS'].get('X-FORWARDED-FOR') or self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
            self.client_address = (host, self.client_address[1])
        env['CONTENT_LENGTH'] = int(self.headers.get('content-length', '0'))
        if len(env['BODY']) != env['CONTENT_LENGTH']:
            env['BODY'] += self.rfile.read(env['CONTENT_LENGTH'] - len(env['BODY']))
        boundary = re.findall(r'boundary=-*([\w]+)', self.headers.get('content-type', ''))  # boundary is used to catch multipart form data (includes file uploads)
        content_type = env['CONTENT_TYPE'].lower()
        if boundary:
            self._get_boundary_enclosed(boundary, env)
        elif content_type == 'application/json' and env['BODY']:
            env[env['REQUEST_METHOD']] = json.loads(env['BODY'])
        elif content_type == 'application/x-www-form-urlencoded':
            env[env['REQUEST_METHOD']] = self._parse_qs(env['BODY'].decode())
        elif content_type == 'multipart/form-data':
            for q in re.sub(r'-{15,}\d+', '+@~!@+', env['BODY'].decode().replace('\n', '')).split('+@~!@+'):
                if '=' in q:
                    q = q.split(';')[1].strip().split('=', 1)[1].replace('"', '').split('\r\r')
                    k, v = [unquote_plus(a) if a else a for a in q]
                    v = v.replace('\r', '')
                    request_method = env[env['REQUEST_METHOD']]
                    if k in request_method:
                        try:
                            request_method[k].append(v)
                        except AttributeError:
                            request_method[k] = [request_method[k], v]
                    else:
                        request_method[k] = v
        if env['QUERY_STRING']:
            env['GET'] = self._parse_qs(env['QUERY_STRING'])
        return env

    def handle(self):
        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline, self.request_version, self.command = '', '', ''
            self.send_error(414)
            return
        if not self.parse_request():
            return
        env = self.get_environ()
        if any(self.server.websocket_handlers.values()):  # only handshakes websockets if there is a function to handle them
            self.handshake(env)
            if self.valid_client:
                while self.keep_alive:
                    self.read_next_message()
                return
        handler = ServerHandler(self.rfile, self.wfile, sys.stderr, env)
        handler.request_handler = self
        handler.run(self.server.application)

    def read_next_message(self):
        """Used to get messages from the websocket"""
        try:
            b1, b2 = self.rfile.read(2)
        except ConnectionResetError as e:
            print(f'Error: {e}')
            self.keep_alive = False
            return
        except ValueError:
            b1, b2 = 0, 0
        opcode = b1 & 0x0f
        payload_length = b2 & 0x7f
        if opcode == 0x8 or not b2 & 0x80:  # disconnect
            self.keep_alive = False
            return
        if opcode == 0x2:  # binary (Not supported)
            return
        elif opcode == 0x1:  # text
            opcode_handler = self.server.message_received
        else:
            self.keep_alive = False
            return
        if payload_length == 126:
            payload_length = struct.unpack(">H", self.rfile.read(2))[0]
        elif payload_length == 127:
            payload_length = struct.unpack(">Q", self.rfile.read(8))[0]
        masks = self.rfile.read(4)
        message_bytes = bytearray()
        for message_byte in self.rfile.read(payload_length):
            message_bytes.append(message_byte ^ masks[len(message_bytes) % 4])
        opcode_handler(self, message_bytes.decode('utf8'))

    def handshake(self, env: dict):
        if env['REQUEST_METHOD'] != 'GET' or env['HEADERS'].get('UPGRADE', '').lower() != 'websocket' or 'sec-websocket-key' not in self.headers:
            return
        self.handshake_done = self.request.send(f'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {b64encode(sha1((self.headers["sec-websocket-key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).strip().decode("ASCII")}\r\n\r\n'.encode())
        self.valid_client = True
        self.server.new_client(self, env)

    def send_message(self, message, opcode: int = 0x1) -> bool:
        """Important: Fragmented(=continuation) messages are not supported since their usage cases are limited - when we don't know the payload length."""
        if isinstance(message, bytes):
            try:
                message = message.decode('utf-8')  # this is slower but ensures we have UTF-8
            except UnicodeDecodeError:
                return False
        elif not isinstance(message, str):
            return False
        header = bytearray()
        payload = message.encode()
        payload_length = len(payload)
        header.append(0x80 | opcode)
        if payload_length <= 125:  # Normal payload
            header.append(payload_length)
        elif 126 <= payload_length <= 65535:  # Extended payload
            header.append(0x7e)
            header.extend(struct.pack(">H", payload_length))
        elif payload_length < 18446744073709551616:  # Huge extended payload
            header.append(0x7f)
            header.extend(struct.pack(">Q", payload_length))
        else:
            raise Exception("Message is too big. Consider breaking it into chunks.")
        try:
            self.request.send(header + payload)
        except Exception as e:
            print(self.client_address, e, message)

    def send_json(self, message):
        self.send_message(json.dumps(message, default=json_serial))

    def finish(self):
        """Websocket disconnect"""
        super().finish()
        self.server.client_left(self)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"{self.address_string()} - [{datetime.now().strftime('%m/%d/%Y %H:%M:%S')}] {format % args}\n")


class ServerHandler(SimpleHandler):
    os_environ = {}

    def close(self):
        """Override to log requests to console."""
        try:
            self.request_handler.log_request((self.status or '').split(' ', 1)[0], self.bytes_sent)
        finally:
            super().close()

    def error_output(self, environ: dict, start_response: Callable) -> List[bytes]:
        """Override to email ADMINS or send debug page."""
        if environ:
            environ = Request(environ)
        er = ExceptionReporter(environ, *sys.exc_info()).get_traceback_html()[0]
        if App._admins and not App.debug and Mail.default_email['host']:
            Mail(f'Internal Server Error: {environ.get("PATH_INFO", "???")}', '\n'.join(str(e) for e in sys.exc_info()), App._admins, html=er.decode()).embed().send()
        start_response(self.error_status, self.error_headers[:] if not App.debug else [('Content-Type', 'text/html')], sys.exc_info())
        return [er] if App.debug else [self.error_body]
