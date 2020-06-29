from os.path import splitext
from typing import Union, Tuple, List
# these types are imported for primarily for typing, and
from watchdog.events import DirMovedEvent, FileMovedEvent, \
    DirCreatedEvent, FileCreatedEvent, \
    DirDeletedEvent, FileDeletedEvent, \
    DirModifiedEvent, FileModifiedEvent

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
        self.default_handler = kwargs.get('default_handler', WatchmanHandler())

    def watch(self, path: str, recursive: bool = False, handler: FileSystemEventHandler = None):
        if handler is None:
            handler = self.default_handler
        watch = self.observer.schedule(handler, path, recursive)
        self.watchlist.append(watch)

    def watch_many(self, paths: List[Union[str, Tuple[str, bool]]], handler: FileSystemEventHandler = None):
        if handler is None:
            handler = self.default_handler
        for path_info in paths:
            path_recursive = False
            if isinstance(path_info, tuple):
                path_str, path_recursive = path_info
            else:
                path_str = path_info
            self.watch(path_str, path_recursive, handler)

    # Ill come up with a better way of doing this later
    def unwatch(self, path: str, recursive: bool = False):

        for watch in self.watchlist:
            if watch.path == path and watch.is_recursive == recursive:
                self.observer.unschedule(watch)
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

    def unwatch_all(self):
        self.observer.unschedule_all()
        self.watchlist.clear()
        return True

    # Data-Design wise it seems Dir*Event and File*Event are identical,
    # but i might need to do different logic for directories than files,
    # so i do a check in  each function


class WatchmanHandler(FileSystemEventHandler):
    def __init__(self):
        pass

    def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]):
        # Directory moved
        if isinstance(event, DirModifiedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError

    def on_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]):
        # Directory moved
        if isinstance(event, DirCreatedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError

    def on_delete(self, event: Union[DirDeletedEvent, FileDeletedEvent]):
        # Directory moved
        if isinstance(event, DirDeletedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError

    def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
        # Directory moved
        if isinstance(event, DirMovedEvent):
            raise NotImplementedError
        # File moved
        else:
            raise NotImplementedError


class WatchmanHandlerPlus(WatchmanHandler):
    def __init__(self, **kwargs):
        super().__init__()
        self.extension_whitelist = kwargs.get('extension_whitelist', None)
        if self.extension_whitelist:
            for i in range(len(self.extension_whitelist)):
                value = self.extension_whitelist[i]
                value = value.lower()
                if len(value) > 0 and value[0] != '.':
                    value = f".{value}"
                self.extension_whitelist[i] = value

    def path_in_whitelist(self, path):
        _, ext = splitext(path)
        self.ext_in_whitelist(ext)

    def ext_in_whitelist(self, extension):
        if self.extension_whitelist is None:
            return True
        else:
            return extension in self.extension_whitelist

    def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
        # Directory moved
        if isinstance(event, DirMovedEvent):
            self.on_dir_renamed(event)
        # File moved
        else:
            if self.path_in_whitelist(event.src_path):
                self.on_file_renamed(event)

    def on_file_renamed(self, event: FileMovedEvent):
        pass

    def on_dir_renamed(self, event: DirMovedEvent):
        pass

    def on_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]):
        # Directory moved
        if isinstance(event, DirCreatedEvent):
            self.on_dir_found(event)
        # File moved
        else:
            if self.path_in_whitelist(event.src_path):
                self.on_file_found(event)

    def on_file_found(self, event: FileCreatedEvent):
        pass

    def on_dir_found(self, event: DirCreatedEvent):
        pass

    def on_deleted(self, event: Union[DirDeletedEvent, FileDeletedEvent]):
        # Directory moved
        if isinstance(event, DirDeletedEvent):
            self.on_dir_lost(event)
        # File moved
        else:
            if self.path_in_whitelist(event.src_path):
                self.on_file_lost(event)

    def on_file_lost(self, event: FileDeletedEvent):
        pass

    def on_dir_lost(self, event: DirDeletedEvent):
        pass

    def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]):
        # Directory moved
        if isinstance(event, DirModifiedEvent):
            self.on_dir_changed(event)
        # File moved
        else:
            if self.path_in_whitelist(event.src_path):
                self.on_file_changed(event)

    def on_file_changed(self, event: FileModifiedEvent):
        pass

    def on_dir_changed(self, event: DirModifiedEvent):
        pass
