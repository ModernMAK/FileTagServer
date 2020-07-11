from argparse import ArgumentParser
from typing import List, Optional

from litespeed.helpers import render, serve
from litespeed.mail import Mail
from litespeed.server import App, RequestHandler, WebServer

route = App.route
add_websocket = App.add_websocket
register_error_page = App.register_error_page
__all__ = ['Mail', 'start_with_args', 'route', 'serve', 'render', 'add_websocket', 'App', 'register_error_page']


def start_server(**kwargs) -> WebServer:
    """
    kwargs:
        bind: str = '0.0.0.0'\n
        port: int = 8000\n
        cors_allow_origin: Union[Iterable, str] = None\n
        cors_methods: Union[Iterable, str] = None\n
        cookie_max_age: int = 7 * 24 * 3600\n
        handler=RequestHandler\n
        serve: bool = True\n
        debug: bool = False\n
        admins: Optional[List[str]] = None\n
        default_email: str = ''\n
        default_email_username: str = ''\n
        default_email_password: str = ''\n
        default_email_host: str = ''\n
        default_email_port: int = 25\n
        default_email_tls: bool = True\n
        default_email_ssl: bool = False\n
        default_email_timeout: int = 0"""
    server = WebServer((kwargs.get('bind', '0.0.0.0'), kwargs.get('port', 8000)), kwargs.get('handler', RequestHandler))
    application = kwargs.get('app', App)
    application.debug = kwargs.get('debug', False)
    server.application = application()
    cors_allow_origin = kwargs.get('cors_allow_origin')
    cors_methods = kwargs.get('cors_methods')
    App._cors_origins_allow = {c.lower() for c in cors_allow_origin} if isinstance(cors_allow_origin, (list, set, dict, tuple)) else {c for c in cors_allow_origin.lower().strip().split(',') if c} if cors_allow_origin else set()
    App._cors_methods_allow = {c.lower() for c in cors_methods} if isinstance(cors_methods, (list, set, dict, tuple)) else {c for c in cors_methods.lower().strip().split(',') if c} if cors_methods else set()
    App._admins = kwargs.get('admins', [])
    App._cookie_age = kwargs.get('max_cookie_age', 7 * 24 * 3600)
    Mail.default_email['from'] = kwargs.get('default_email', '')
    Mail.default_email['username'] = kwargs.get('default_email_username', '')
    Mail.default_email['password'] = kwargs.get('default_email_password', '')
    Mail.default_email['host'] = kwargs.get('default_email_host', '')
    Mail.default_email['port'] = kwargs.get('default_email_port', 25)
    Mail.default_email['tls'] = kwargs.get('default_email_tls', True)
    Mail.default_email['ssl'] = kwargs.get('default_email_ssl', False)
    Mail.default_email['timeout'] = kwargs.get('default_email_timeout', 0)
    if kwargs.get('serve', True):
        server.serve()
    return server


def start_with_args(bind_default: str = '0.0.0.0', port_default: int = 8000, cors_allow_origin: str = '', cors_methods: str = '', cookie_max_age: int = 7 * 24 * 3600, serve: bool = True, debug: bool = False, admins: Optional[List[str]] = None, **kwargs) -> WebServer:
    """Allows you to specify a lot of parameters for start_server

    kwargs:
        from_email: str = ''\n
        from_username: str = ''\n
        from_password: str = ''\n
        from_host: str = ''\n
        from_port: int = 25\n
        from_tls: bool = True\n
        from_ssl: bool = False\n
        from_timeout: int = 0"""
    parser = ArgumentParser()
    parser.add_argument('-b', '--bind', default=bind_default)
    parser.add_argument('-p', '--port', default=port_default, type=int)
    parser.add_argument('--cors_allow_origin', default=cors_allow_origin)
    parser.add_argument('--cors_methods', default=cors_methods)
    parser.add_argument('--cookie_max_age', default=cookie_max_age)
    parser.add_argument('-d', '--debug', action='store_true', default=debug)
    parser.add_argument('-a', '--admins', action='append', default=admins)
    parser.add_argument('--default_email', default=kwargs.get('from_email', None))
    parser.add_argument('--default_email_username', default=kwargs.get('from_username', None))
    parser.add_argument('--default_email_password', default=kwargs.get('from_password', None))
    parser.add_argument('--default_email_host', default=kwargs.get('from_host', None))
    parser.add_argument('--default_email_port', default=kwargs.get('from_port', None), type=int)
    parser.add_argument('--default_email_tls', default=kwargs.get('from_tls', None), action='store_true')
    parser.add_argument('--default_email_ssl', default=kwargs.get('from_ssl', None), action='store_true')
    parser.add_argument('--default_email_timeout', default=kwargs.get('from_timeout', None), type=int)
    return start_server(app=kwargs.get('app', App), **parser.parse_args().__dict__, serve=serve)


if __name__ == '__main__':  # example index page (does not have to be in __name__=='__main__')
    @App.route()
    def index(request):
        return [b'Not Implemented']


    # routes should be declared before start_server or start_with_args because start_server will block until shutdown
    start_with_args()
