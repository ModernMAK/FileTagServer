from litespeed import start_with_args
from src import DbUtil

if __name__ == '__main__':
    DbUtil.initialize_db()
    start_with_args()
