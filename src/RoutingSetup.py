import src.Routing.VirtualAccessPoints as Vap
import src.Routing.API as api
import src.Routing.REST as rest
import src.Routing.WebPages as WebPages


def init():
    Vap.init()
    api.add_routes()
    rest.add_routes()
    WebPages.init()
