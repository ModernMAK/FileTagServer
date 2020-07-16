import os
from typing import Callable, Tuple, Any, Dict

from litespeed import route, serve
from src.util import path_util


class VirtualAccessPoints:
    lookup = {}

    @classmethod
    def register_vap(cls, name: str, real_path: str, virtual_path: str,
                     function: Callable[[Any], Tuple[bytes, int, Dict[str, str]]]) -> None:
        real_path.replace("%ROOT%", path_util.project_root())
        virtual_path = virtual_path.replace('\\', '/')
        cls.lookup[name] = {
            'real': real_path,
            'route': f"{virtual_path}/(.*)",
            'virtual': virtual_path,
            'function': function
        }

    @classmethod
    def get(cls, name: str, default: Any = None):
        return cls.lookup.get(name, default)

    @classmethod
    def get_real_path(cls, name: str, default: Any = None):
        return cls.lookup.get(name, {}).get('real', default)

    @classmethod
    def get_virtual_path(cls, name: str, default: Any = None):
        return cls.lookup.get(name, {}).get('virtual', default)

    @classmethod
    def add_routes(cls):
        for vap_data in cls.lookup.values():
            r_path, func = vap_data['route'], vap_data['function']
            route(r_path, function=func, no_end_slash=True, methods=['GET'])


class RequiredVap:
    html_real_def = os.path.join(path_util.project_root(), 'web', 'html')

    @classmethod
    def html_real(cls, local_file: str):
        return os.path.join(cls.html_real_def, local_file)

    @classmethod
    def html_virtual(cls, local_file: str):
        raise NotImplementedError

    data_real_def = os.path.join(path_util.project_root(), 'web', 'data')

    @classmethod
    def data_real(cls, local_file: str):
        return os.path.join(cls.data_real_def, local_file)

    @classmethod
    def data_virtual(cls, local_file: str):
        raise NotImplementedError

    dynamic_generated_real_def = os.path.join(path_util.project_root(), 'web', 'dynamic', 'generated')
    dynamic_generated_virtual_def = "/" + os.path.join('', 'dyn', 'gen')

    @classmethod
    def dynamic_generated_real(cls, local_file: str):
        return os.path.join(cls.dynamic_generated_real_def, local_file)

    @classmethod
    def dynamic_generated_virtual(cls, local_file: str):
        return os.path.join(cls.dynamic_generated_virtual_def, local_file)

    file_html_real_def = os.path.join(html_real_def, 'file')

    @classmethod
    def file_html_real(cls, local_file: str):
        return os.path.join(cls.file_html_real_def, local_file)

    rest_html_real_def = os.path.join(html_real_def, 'rest')

    @classmethod
    def rest_html_real(cls, local_file: str):
        return os.path.join(cls.rest_html_real_def, local_file)

    css_real_def = os.path.join(path_util.project_root(), 'web', 'css')
    css_virtual_def = "/" + 'css'

    @classmethod
    def css_real(cls, local_file: str):
        return os.path.join(cls.css_real_def, local_file)

    @classmethod
    def css_virtual(cls, local_file: str):
        return os.path.join(cls.css_virtual_def, local_file)

    js_real_def = os.path.join(path_util.project_root(), 'web', 'js')
    js_virtual_def = "/" + 'js'

    @classmethod
    def js_real(cls, local_file: str):
        return os.path.join(cls.css_real_def, local_file)

    @classmethod
    def js_virtual(cls, local_file: str):
        return os.path.join(cls.css_virtual_def, local_file)

    @classmethod
    def add_to_vap(cls):
        def get_serve(r_path):
            def internal_serve(request, page):
                headers = {}
                if request is not None:
                    range = request.get('HEADERS').get('RANGE')
                    if range is not None:
                        headers = {'RANGE': range}

                return serve(os.path.join(r_path, page), range=range)

            return internal_serve

        def register_helper(name: str, real: str, virtual: str):
            VirtualAccessPoints.register_vap(name, real, virtual, get_serve(real))

        register_helper('dynamic_generated', cls.dynamic_generated_real_def, cls.dynamic_generated_virtual_def)
        register_helper('css', cls.css_real_def, cls.css_virtual_def)
        register_helper('js', cls.js_real_def, cls.js_virtual_def)
