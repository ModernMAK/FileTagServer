from os.path import join

from litespeed import serve, route

from src.util.litespeedx import Request, Response


class StaticHelper:
    def __init__(self, local_path: str, web_path: str):
        self.path = local_path
        self.route = web_path

    def resolve_route(self, part: str) -> str:
        return self.route.replace("(.*)", part)

    def resolve_path(self, part: str) -> str:
        return join(self.path, part)


html = StaticHelper("static/html", "html/(.*)")
js = StaticHelper("static/js", "js/(.*)")
css = StaticHelper("static/css", "css/(.*)")


def __static(request: Request, root: str, path: str) -> Response:
    full_path = join(root, path)
    range = request['HEADERS'].get('Range')
    return serve(full_path, range, {"Accept-Ranges": "bytes"})


@route(html.route, ['GET'], no_end_slash=True)
def _html(request: Request, path: str):
    return __static(request, html.path, path)


@route(js.route, ['GET'], no_end_slash=True)
def _js(request: Request, path: str):
    return __static(request, js.path, path)


@route(css.route, ['GET'], no_end_slash=True)
def _css(request: Request, path: str):
    return __static(request, css.path, path)

#
# # serves the file; using the path function to resolve the full path
# @staticmethod
# def __serve_path_func(path_func: Callable[[str], str]) -> ServeFunction:
#     def __internal(request, path: str) -> ServeResponse:
#         print(path_func(path))
#         return serve(path_func(path))
#
#     return __internal
#
#
# @classmethod
# def add_routes(cls):
#     # capture everything after our text
#     capture_regex = "(.*)"
#     route(
#         routing.Static.get_css(capture_regex),
#         function=cls.__serve_path_func(pathing.Static.get_css),
#         no_end_slash=True,
#         methods=['GET'])
#
#     route(routing.Static.get_javascript(capture_regex),
#           function=cls.__serve_path_func(pathing.Static.get_javascript),
#           no_end_slash=True,
#           methods=['GET'])
#
#     route(routing.Static.get_image(capture_regex),
#           function=cls.__serve_path_func(pathing.Static.get_image),
#           no_end_slash=True,
#           methods=['GET'])
#
#
# class Static:
#
#     @classmethod
#     def get_css(cls, path_or_regex: str) -> str:
#         return web_join(cls.css, path_or_regex)
#
#     @classmethod
#     def get_javascript(cls, path_or_regex: str) -> str:
#         return web_join(cls.js, path_or_regex)
#
#     @classmethod
#     def get_image(cls, path_or_regex: str) -> str:
#         return web_join(cls.image, path_or_regex)
#
#
# # This is primarily for me to group constants together
# # None of these classes should be instantiated
# def append_get_args(path: str, **kwargs) -> str:
#     args = []
#     for keyword in kwargs:
#         value = kwargs[keyword]
#         # TODO sanitize keyword and value
#         args.append(f"{keyword}={value}")
#
#     if len(args) > 0:
#         return path + "?" + "&".join(args)
#     return path
#
#
# def web_join(*args) -> str:
#     # Join on my system inserts \\
#     # which works great for file systems
#     # but bad for a regex parsing html paths
#     # (which route does to allow capturing certain portions of the path)
#     return join(*args).replace('\\', '/')
#
#
# def full_path(path: str, protocol: str = None):
#     if protocol is None:
#         protocol = "http"
#
#     if path[0] == WebRoot.root:
#         return f"{protocol}://" + WebRoot.domain + path
#     else:
#         return path
#
#
# # It may be dumb to have this all by itself, BUT
# # makes it easier to differentiate this root from the other roots in this file
# # also, i dont have to type global root
# class WebRoot:
#     domain = "localhost:8000"
#     root = "/"
#
#
# class Static:
#     root = WebRoot.root
#     html = web_join(root, "html")
#     image = join(root, "img")
#     js = web_join(root, "js")
#     css = web_join(root, "css")
#
#     @classmethod
#     def get_css(cls, path_or_regex: str) -> str:
#         return web_join(cls.css, path_or_regex)
#
#     @classmethod
#     def get_javascript(cls, path_or_regex: str) -> str:
#         return web_join(cls.js, path_or_regex)
#
#     @classmethod
#     def get_image(cls, path_or_regex: str) -> str:
#         return web_join(cls.image, path_or_regex)
#
#
# class FilePage:
#     root = web_join(WebRoot.root, "file")
#     view_file = web_join(root, "view")
#     edit_file = web_join(root, "edit")
#     index_list = web_join(root, "list")
#     serve_file_raw = web_join(root, "raw")
#     serve_page_raw = web_join(root, "rawpage")
#     slideshow = web_join(root, "slideshow")
#
#     @classmethod
#     def get_view_file(cls, id: int):
#         return append_get_args(cls.view_file, id=id)
#
#     @classmethod
#     def get_index_list(cls, page: int = None, size: int = None, search: str = None):
#         get_args = {}
#         if page is not None:
#             get_args['page'] = page
#         if size is not None:
#             get_args['size'] = size
#         if search is not None:
#             get_args['search'] = search
#
#         return append_get_args(cls.index_list, **get_args)
#
#     @classmethod
#     def get_serve_file_raw(cls, id: int):
#         return append_get_args(cls.serve_file_raw, id=id)
#
#     @classmethod
#     def get_serve_page_raw(cls, id: int):
#         return append_get_args(cls.serve_page_raw, id=id)
#
#     @classmethod
#     def get_edit_file(cls, id: int):
#         return append_get_args(cls.edit_file, id=id)
#
#
# class ApiPage:
#     root = web_join(WebRoot.root, "api")
#
#     file_root = web_join(root, "file")
#     file_list = web_join(file_root, "list")
#     file_data = web_join(file_root, "data")
#
#     tag_root = web_join(root, "tag")
#     tag_list = web_join(file_root, "list")
#     tag_autocorrect = web_join(file_root, "autocorrect")
#
#     @classmethod
#     def get_file_list(cls, format: str = "json", page: int = None, size: int = None, search: str = None):
#         file_path = f"{cls.file_list}.{format}"
#         get_args = {}
#         if page is not None:
#             get_args['page'] = page
#         if size is not None:
#             get_args['size'] = size
#         if search is not None:
#             get_args['search'] = search
#         return append_get_args(file_path, **get_args)
#
#     @classmethod
#     def get_file_data(cls, format: str = "json"):
#         file_path = f"{cls.file_data}.{format}"
#         return append_get_args(file_path)
#
#     @classmethod
#     def get_tag_list(cls, format: str = "json"):
#         file_path = f"{cls.tag_list}.{format}"
#         return append_get_args(file_path)
#
#     @classmethod
#     def get_tag_autocorrect(cls, format: str = "json"):
#         file_path = f"{cls.tag_autocorrect}.{format}"
#         return append_get_args(file_path)
#
#
# class TagPage:
#     root = web_join(WebRoot.root, "tag")
#     view_tag = web_join(root, "view")
#     index_list = web_join(root, "list")
#
#     @classmethod
#     def get_view_tag(cls, id: int):
#         return append_get_args(cls.view_tag, id=id)
#
#     @classmethod
#     def get_index_list(cls, page: int):
#         return append_get_args(cls.index_list, page=page)
#
#
# class UploadPage:
#     root = web_join(WebRoot.root, "upload")
#     action_root = web_join(root, "action")
#
#     upload_file = web_join(root, "file")
#     action_upload_file = web_join(action_root, "file")
#
#     add_file = web_join(root, "path")
#     action_add_file = web_join(action_root, "path")
