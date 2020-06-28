from litespeed import start_with_args
from src import DbMediator
import src.Routing.VirtualAccessPoints as Vap
import src.Routing.API as api
import src.Routing.REST as rest
import src.Routing.WebPages as WebPages

if __name__ == '__main__':
    DbMediator.initialize_db()
    Vap.add_routes()
    api.add_routes()
    rest.add_routes()
    WebPages.add_routes()
    start_with_args()
