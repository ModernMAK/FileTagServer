from os.path import join

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_oauth2_redirect_html, get_swagger_ui_html
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from pystache import renderer

rest_api = FastAPI(docs_url=None, redoc_url=None)

# Docs url is handled here
renderer = renderer.Renderer(search_dirs="../static/html/doc")

rest_api.mount("/js", StaticFiles(directory="../static/js"), name="JavaScript")
rest_api.mount("/css", StaticFiles(directory="../static/css"), name="Cascading Style Sheets")


def initialize_routes(root: str = None):
    root = root or ""
    swagger_ui_route = f"{root}/docs"
    redoc_route = f"{root}/redoc"
    index_route = root + "/"

    @rest_api.get(index_route, include_in_schema=False)
    def index():
        context = {'swagger_ui_route': swagger_ui_route, 'redoc_route': redoc_route}
        html = renderer.render_path(r"../static/html/docs/index.html", **context)
        return HTMLResponse(html)

    @rest_api.get(swagger_ui_route, include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=rest_api.openapi_url,
            title=rest_api.title + " - Swagger UI",
            oauth2_redirect_url=rest_api.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/js/docs/swagger-ui-bundle.js",
            swagger_css_url="/css/docs/swagger-ui.css",
        )

    @rest_api.get(rest_api.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @rest_api.get(redoc_route, include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=rest_api.openapi_url,
            title=rest_api.title + " - ReDoc",
            redoc_js_url="/js/docs/redoc.standalone.js",
        )
