from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_oauth2_redirect_html, get_swagger_ui_html
from starlette.staticfiles import StaticFiles

rest_api = FastAPI(docs_url=None, redoc_url=None)


# Docs url is handled here

rest_api.mount("/js", StaticFiles(directory="../static/doc"), name="JavaScript")
rest_api.mount("/css", StaticFiles(directory="../static/doc"), name="Cascading Style Sheets")


@rest_api.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=rest_api.openapi_url,
        title=rest_api.title + " - Swagger UI",
        oauth2_redirect_url=rest_api.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/js/swagger-ui-bundle.js",
        swagger_css_url="/css/swagger-ui.css",
    )


@rest_api.get(rest_api.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@rest_api.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=rest_api.openapi_url,
        title=rest_api.title + " - ReDoc",
        redoc_js_url="/js/redoc.standalone.js",
    )
