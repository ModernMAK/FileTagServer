from litespeed import start_with_args
from src import DbMediator, RoutingSetup

if __name__ == '__main__':
    DbMediator.initialize_db()
    RoutingSetup.init()
    start_with_args()
