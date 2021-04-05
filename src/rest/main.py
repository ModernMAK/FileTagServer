from litespeed import route, start_with_args, App

from src.rest.common import url_join, url_protocol
from src.rest.routes import finalize_routes
from src.rest import file, tag

if __name__ == '__main__':
    finalize_routes()


    @route("/")
    def index(request):
        urls = {url_protocol("http", url_join("localhost", u.url)) for u in App._urls}

        return {'urls': urls}


    start_with_args(port_default=80)
