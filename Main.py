from litespeed import start_with_args
from src import DbUtil, RoutingSetup

if __name__ == '__main__':
    DbUtil.initialize_db()
    RoutingSetup.init()
    start_with_args()
