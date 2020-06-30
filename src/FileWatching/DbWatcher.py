import configparser
import os
from os.path import splitext, exists
from typing import Union

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileMovedEvent, FileDeletedEvent
from functools import partial
from src.WatchMan import Watchman, WatchmanHandlerPlus


class DatabaseWatchHandler(WatchmanHandlerPlus):
    # update_callback: Union[None, Callable[[int, str], Any]]
    # add_callback: Union[None, Callable[[str], int]]
    # get_callback: Union[None, Callable[[str], Union[None,int]]]
    def __init__(self, **kwargs):
        super().__init__()
        self.update_callback = kwargs.get('update_callback')
        self.add_callback = kwargs.get('add_callback')
        self.get_callback = kwargs.get('get_callback')

    @staticmethod
    def __is_meta(path: str):
        _, ext = splitext(path)
        return ext.lower() == '.meta'

    @staticmethod
    def __get_meta_path(path: str):
        return path + '.meta'

    @staticmethod
    def __get_file_path(path: str):
        file, _ = splitext(path)
        return file

    @staticmethod
    def __read_meta(metadata) -> Union[None, int]:
        try:
            parser = configparser.SafeConfigParser()
            parser.read_string(metadata)
            return int(parser.get('File', 'id'))
        except configparser.NoSectionError:
            return None

    def on_file_lost(self, event: FileDeletedEvent):
        file_path = event.src_path
        meta_path = file_path
        if DatabaseWatchHandler.__is_meta(file_path):
            file_path = DatabaseWatchHandler.__get_file_path(meta_path)
            # Recreate meta
            self.__perform_get(file_path, meta_path)

    def on_file_found(self, event: FileCreatedEvent):
        file_path = event.src_path
        meta_path = file_path
        if DatabaseWatchHandler.__is_meta(file_path):
            file_path = DatabaseWatchHandler.__get_file_path(meta_path)
        else:
            meta_path = DatabaseWatchHandler.__get_meta_path(meta_path)

        self.__found_logic(file_path, meta_path)

    def on_file_renamed(self, event: FileMovedEvent):
        old = event.src_path
        new = event.dest_path
        if DatabaseWatchHandler.__is_meta(old):
            return
        try:
            old_meta = DatabaseWatchHandler.__get_meta_path(old)
            new_meta = DatabaseWatchHandler.__get_meta_path(new)
            os.rename(old_meta, new_meta)
        except FileNotFoundError:
            return

    def on_file_modified(self, event: FileModifiedEvent):
        file_path = event.src_path
        meta_path = file_path
        if DatabaseWatchHandler.__is_meta(file_path):
            file_path = DatabaseWatchHandler.__get_file_path(meta_path)
        else:
            return

        self.__found_logic(file_path, meta_path)

    def __write_meta(self, meta_path: str, id: int):
        parser = configparser.ConfigParser()
        try:
            with open(meta_path, 'r') as meta_f:
                parser.read_file(meta_f)
        except FileNotFoundError:
            pass
        with open(meta_path, 'w') as meta_f:
            if 'File' not in parser.sections():
                parser.add_section('File')
            parser.set('File', 'id', str(id))
            parser.write(meta_f)

    def __perform_get(self, data_path: str, meta_path: str):
        if not exists(data_path):
            return
        if self.get_callback is not None:
            id = self.get_callback(data_path)
            if id is None:
                self.__perform_add(data_path, meta_path)
            else:
                self.__write_meta(meta_path, id)
        else:
            raise NotImplementedError

    def __perform_add(self, data_path: str, meta_path: str):
        if self.add_callback is not None:
            id = self.add_callback(data_path)
            self.__write_meta(meta_path, id)
        else:
            raise NotImplementedError

    def __found_logic(self, data_path: str, meta_path: str):
        if not exists(data_path):
            return

        try:
            with open(meta_path, 'r') as meta_f:
                metadata = meta_f.read()
                result = DatabaseWatchHandler.__read_meta(metadata)
                if result is None:
                    # TODO
                    # handle invalid meta?
                    self.__perform_add(data_path, meta_path)
                else:
                    # TODO
                    # update the database
                    if self.update_callback is not None:
                        self.update_callback(result, data_path)
                    else:
                        raise NotImplementedError
        except FileNotFoundError:
            # TODO
            # Add to the database
            # Create metadata
            self.__perform_add(data_path, meta_path)


def create_test_watchman(**kwargs):
    class helper:
        def __init__(self):
            self.lookup = {}

        def update(self):
            return partial(self.__log_update)

        def add(self):
            return partial(self.__log_add)

        def get(self):
            return partial(self.__log_get)

        def __log_update(self, id: int, path: str):
            print(f"UPDATE: {path} ~ {id}")
            self.lookup[path] = id

        def __log_add(self, path: str) -> int:
            values = self.lookup.values()
            u_values = set(values)
            next_value = 0
            while next_value in u_values:
                next_value += 1
            print(f"ADD: {path} ~ {next_value}")
            self.lookup[path] = next_value
            return next_value

        def __log_get(self, path: str) -> Union[int, None]:
            value = self.lookup.get(path, None)
            print(f"GET: {path} ~ {value}")
            return value

    temp = helper()
    update_callback = kwargs.get('update_callback', temp.update())
    add_callback = kwargs.get('add_callback', temp.add())
    get_callback = kwargs.get('get_callback', temp.get())

    handler = DatabaseWatchHandler(update_callback=update_callback, add_callback=add_callback,
                                   get_callback=get_callback)
    return Watchman(default_handler=handler)


def create_database_watchman(**kwargs):
    class GetAsd:
        def __init__(self):
            self.lookup = {}

        def update(self):
            return partial(self.__log_update)

        def add(self):
            return partial(self.__log_add)

        def get(self):
            return partial(self.__log_get)

        def __log_update(self, id: int, path: str):
            print(f"UPDATE: {path} ~ {id}")
            self.lookup[path] = id

        def __log_add(self, path: str) -> int:
            values = self.lookup.values()
            u_values = set(values)
            next_value = 0
            while next_value in u_values:
                next_value += 1
            print(f"ADD: {path} ~ {next_value}")
            self.lookup[path] = next_value
            return next_value

        def __log_get(self, path: str) -> Union[int, None]:
            value = self.lookup.get(path, None)
            print(f"GET: {path} ~ {value}")
            return value

    temp = GetAsd()
    update_callback = kwargs.get('update_callback', temp.update())
    add_callback = kwargs.get('add_callback', temp.add())
    get_callback = kwargs.get('get_callback', temp.get())

    handler = DatabaseWatchHandler(update_callback=update_callback, add_callback=add_callback,
                                   get_callback=get_callback)
    return Watchman(default_handler=handler)