import src.Routing.VirtualAccessPoints as Vap
import src.Routing.API as Rest
import src.Routing.WebPages as WebPages


def init():
    Vap.init()
    Rest.add_routes()
    WebPages.init()
