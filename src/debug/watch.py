from time import sleep
from src.PathUtil import root_path
from watchdog.events import LoggingEventHandler

from src.WatchMan import Watchman, FileSystemEventHandler, DirMovedEvent, DirDeletedEvent, DirCreatedEvent


class SimpleLogHandler(FileSystemEventHandler):
    def __init__(self):
        pass

    def on_created(self, event: DirCreatedEvent):
        print(f'Created: "{event.src_path}"')

    def on_deleted(self, event: DirDeletedEvent):
        print(f'Deleted: "{event.src_path}"')

    def on_modified(self, event):
        print(f'Modified "{event.src_path}"')

    def on_moved(self, event: DirMovedEvent):
        print(f'Moved "{event.src_path}" to "{event.dest_path}"')


if __name__ == '__main__':

    handler = SimpleLogHandler()
    watcher = Watchman(default_handler=handler)
    paths = ['debug/watch_me/New Text Document.txt', 'debug/watch_me/test.txt','debug/watch_me']
    # watcher.watch(root_path('debug/watch_me'), True)
    print('Watching:')
    for path in paths:
        rooted_path = root_path(path)
        print("\t" + rooted_path)
        watcher.watch(rooted_path, False, handler)
    print('Watch Started')
    watcher.observer.start()
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        watcher.observer.stop()
    watcher.observer.join()
    print('Watch Ended')
