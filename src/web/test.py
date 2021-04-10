from litespeed import serve, route, App, start_with_args

from src.rest.common import serve_json, url_protocol, url_join
from src.rest.main import finalize_routes


@route("test",no_end_slash=True)
def test(request):
    return serve("src/web/test.html")


if __name__ == '__main__':
    finalize_routes()


    @route("/")
    def index(request):
        urls = {u.url: {'url': url_protocol("http", url_join("localhost", u.url)), 'methods': []} for u in App._urls}
        for u in App._urls:
            urls[u.url]['methods'].extend(u.methods)
        urls = list(urls.values())
        urls.sort(key=lambda d: d['url'])
        return serve_json(urls)


    start_with_args(port_default=80)
