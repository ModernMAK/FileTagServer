# from os.path import join
#
# # from litespeed import serve, route
#
# from src.util.litespeedx import Request, Response
#
#
# class StaticHelper:
#     def __init__(self, local_path: str, web_path: str):
#         self.path = local_path
#         self.route = web_path
#
#     def resolve_route(self, part: str) -> str:
#         return self.route.replace("(.*)", part)
#
#     def resolve_path(self, part: str) -> str:
#         return join(self.path, part)
#
#
# # html = StaticHelper("static/html", "html/(.*)")
# # js = StaticHelper("static/js", "js/(.*)")
# # css = StaticHelper("static/css", "css/(.*)")
# #
# #
# # def __static(request: Request, root: str, path: str) -> Response:
# #     full_path = join(root, path)
# #     range = request['HEADERS'].get('Range')
# #     return serve(full_path, range, {"Accept-Ranges": "bytes"})
# #
# #
# # @route(html.route, ['GET'], no_end_slash=True)
# # def _html(request: Request, path: str):
# #     return __static(request, html.path, path)
# #
# #
# # @route(js.route, ['GET'], no_end_slash=True)
# # def _js(request: Request, path: str):
# #     return __static(request, js.path, path)
# #
# #
# # @route(css.route, ['GET'], no_end_slash=True)
# # def _css(request: Request, path: str):
# #     return __static(request, css.path, path)
