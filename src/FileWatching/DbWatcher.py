import configparser
import os
from os.path import splitext, exists
from typing import Union

import PIL
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileMovedEvent, FileDeletedEvent
from functools import partial

from src import PathUtil
from src.ImageUtil import convert_to_imageset
from src.WatchMan import Watchman, WatchmanHandlerPlus
from src.DbUtil import sanitize, Conwrapper

FILE_DEBUG_MODE = True

class DatabaseWatchHandler(WatchmanHandlerPlus):
    # update_callback: Union[None, Callable[[int, str], Any]]
    # add_callback: Union[None, Callable[[str], int]]
    # get_callback: Union[None, Callable[[str], Union[None,int]]]
    # gen_content_callback: Union[None, Callable[[str], bool]
    def __init__(self, **kwargs):
        super().__init__()
        self.update_callback = kwargs.get('update_callback')
        self.add_callback = kwargs.get('add_callback')
        self.get_callback = kwargs.get('get_callback')
        self.gen_content_callback = kwargs.get('gen_content_callback')

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
        if FILE_DEBUG_MODE:
            print(f"LOST: {event.src_path}")
        file_path = event.src_path
        meta_path = file_path
        if DatabaseWatchHandler.__is_meta(file_path):
            file_path = DatabaseWatchHandler.__get_file_path(meta_path)
            # Recreate meta
            self.__perform_get(file_path, meta_path)

    def on_file_found(self, event: FileCreatedEvent):
        if FILE_DEBUG_MODE:
            print(f"FOUND: {event.src_path}")
        file_path = event.src_path
        meta_path = file_path
        if DatabaseWatchHandler.__is_meta(file_path):
            file_path = DatabaseWatchHandler.__get_file_path(meta_path)
        else:
            meta_path = DatabaseWatchHandler.__get_meta_path(meta_path)

        self.__found_logic(file_path, meta_path)

    def on_file_renamed(self, event: FileMovedEvent):
        if FILE_DEBUG_MODE:
            print(f"RENAMED: {event.src_path} -> {event.dest_path}")
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
        if FILE_DEBUG_MODE:
            print(f"MODIFIED: {event.src_path}")
        file_path = event.src_path
        meta_path = file_path
        if DatabaseWatchHandler.__is_meta(file_path):
            file_path = DatabaseWatchHandler.__get_file_path(meta_path)
        else:
            if self.gen_content_callback is not None:
                self.gen_content_callback(file_path)
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


class DatabaseWatchCallbacks:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path')

    def get_args(self, **kwargs):
        kwargs['update_callback'] = partial(self.update_file_path)
        kwargs['add_callback'] = partial(self.add_file)
        kwargs['get_callback'] = partial(self.get_file)
        kwargs['gen_content_callback'] = partial(self.gen_content_for_file)
        return kwargs

    def update_file_path(self, id: int, new_path: str):
        new_path = sanitize(new_path)
        id = int(id)
        query = f"UPDATE FILE SET path = {new_path} where id = {id}"
        with Conwrapper(db_path=self.db_path) as (conn, cursor):
            cursor.execute(query)
            conn.commit()

    def add_file(self, path: str):
        _, ext = splitext(path)
        ext = sanitize(ext.lstrip('.'))
        path = sanitize(path)
        with Conwrapper(db_path=self.db_path) as (conn, cursor):
            query = f"INSERT INTO FILE (path, extension) VALUES ({path}, {ext})"
            cursor.execute(query)
            file_id = int(cursor.lastrowid)
            query = f"INSERT INTO PAGE default values"
            cursor.execute(query)
            page_id = int(cursor.lastrowid)
            query = f"INSERT INTO file_page (page_id, file_id)  values (page_id, file_id)"
            cursor.execute(query)
            conn.commit()
            return file_id

    def get_file(self, path: str) -> Union[int, None]:
        path = sanitize(path)
        with Conwrapper(db_path=self.db_path) as (conn, cursor):
            query = f"SELECT id from file where path = {path}"
            cursor.execute(query)
            result = cursor.fetch()
            if result is not None:
                (file_id,) = result
                return file_id

    def gen_content_for_file(self, path: str) -> bool:
        id = self.get_file(path)
        if id is None:
            return False
        gen_folder = PathUtil.dynamic_generated_real_path(f'file/{int(id)}')
        try:
            real_path = path
            _, ext = splitext(real_path)
            with PIL.Image.open(real_path) as img:
                convert_to_imageset(img, gen_folder, ext)
        except PIL.UnidentifiedImageError:
            pass
        return True


class TestDbCallback:
    def __init__(self, **kwargs):
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
    db_path = kwargs.get('config', {}).get('Launch Args', {}).get('db_path', kwargs.get('db_path',PathUtil.data_real_path('mediaserver2.db')))
    temp = DatabaseWatchCallbacks(db_path=db_path)
    handler_kwargs = temp.get_args()
    handler = DatabaseWatchHandler(**handler_kwargs)
    return Watchman(default_handler=handler)
