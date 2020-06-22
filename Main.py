from litespeed import start_with_args
import DbUtil
import Routing

if __name__ == '__main__':
    DbUtil.initialize_db()
    start_with_args()
