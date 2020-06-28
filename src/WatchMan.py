from typing import Union, Tuple, List
# these types are imported for primarily for typing, and
from watchdog.events import DirMovedEvent, FileMovedEvent, DirCreatedEvent, FileCreatedEvent, DirDeletedEvent, \
    FileDeletedEvent

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# The watchman, keeper of the watchdogs
# Honestly i know why its a watchdog,
# but im also disapointed i cant make a who watches the watchmen joke
# Also this wrapper tracks individual watches to make
class Watchman:
    def __init__(self, **kwargs):
        self.observer = kwargs.get('observer', Observer())
        self.watchlist = []
        self.default_handler = Watchman.__create_handler()

    def watch(self, path: str, recursive: bool = False):
        watch = self.observer.schedule(self.default_handler, path, recursive)
        cache_data = {
            'path': path,
            'recursive': recursive,
            'watch': watch
        }
        self.watchlist.append(cache_data)

    def watch_many(self, paths: List[Union[str, Tuple[str, bool]]]):
        handler = self.default_handler
        for path_info in paths:
            path_str = ''
            path_recursive = False
            if isinstance(path_info, tuple):
                path_str, path_recursive = path_info
            else:
                path_str = path_info
            self.watch(path_str, path_recursive)

    # Ill come up with a better way of doing this later
    def unwatch(self, path: str, recursive: bool = False):
        for watch in self.watchlist:
            if watch['path'] == path and watch['recursive'] == recursive:
                self.observer.unschedule(watch['watch'])
                return True
        return False

    # Ill come up with a better way of doing this later
    def unwatch_many(self, paths: List[Union[str, Tuple[str, bool]]]):
        results = []
        for path_info in paths:
            if isinstance(path_info, tuple):
                path_str, path_recursive = path_info
            else:
                path_str, path_recursive = path_info, False
            results.append(self.unwatch(path_str, path_recursive))
        return results

    def __create_handler(self):
        handler = FileSystemEventHandler()
        handler.on_moved += self.on_file_moved
        handler.on_created += self.on_file_created
        handler.on_deleted += self.on_file_delete
        return handler

    # Data-Design wise it seems Dir*Event and File*Event are identical,
    # but i might need to do different logic for directories than files,
    # so i do a check in  each function

    def on_file_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
        # Directory moved
        if isinstance(event, DirMovedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError

    def on_file_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]):
        # Directory moved
        if isinstance(event, DirCreatedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError

    def on_file_delete(self, event: Union[DirDeletedEvent, FileDeletedEvent]):
        # Directory moved
        if isinstance(event, DirDeletedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError
