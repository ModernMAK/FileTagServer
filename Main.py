from litespeed import start_with_args
from src import DbUtil, Routing

if __name__ == '__main__':
    DbUtil.initialize_db()
    Routing.initializeModule()
    start_with_args()
