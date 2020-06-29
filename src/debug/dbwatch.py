from time import sleep
from src.PathUtil import root_path
from watchdog.events import LoggingEventHandler

from src.WatchMan import Watchman, FileSystemEventHandler, DirMovedEvent, DirDeletedEvent, DirCreatedEvent
import src.DbWatcher as DbWatcher

if __name__ == '__main__':
    watcher = DbWatcher.create_database_watchman()
    paths = ['debug/watch_me/']
    # watcher.watch(root_path('debug/watch_me'), True)
    print('Watching:')
    for path in paths:
        rooted_path = root_path(path)
        print("\t" + rooted_path)
        watcher.watch(rooted_path, True)
    print('Watch Started')
    watcher.observer.start()
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        watcher.observer.stop()
    watcher.observer.join()
    print('Watch Ended')
