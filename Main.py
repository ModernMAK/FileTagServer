from time import sleep
from typing import List

from litespeed import start_with_args
import src.Routing.virtual_access_points as Vap
import src.Routing.rest as rest
import src.Routing.web_pages as WebPages
import configparser
import src.FileWatching.db_watcher as DbWatcher
import src.dbmaintanence as DbMaintenence


def configparser_as_dict(config):
    """
    https://stackoverflow.com/questions/1773793/convert-configparser-items-to-dictionary
    ~ James Kyle
    Converts a ConfigParser object into a dictionary.

    The resulting dictionary has sections as keys which point to a dict of the
    sections options as key => value pairs.
    """
    the_dict = {}
    for section in config.sections():
        the_dict[section] = {}
        for key, val in config.items(section):
            the_dict[section][key] = val
    return the_dict


def ini_str_to_list(text: str) -> List[str]:
    return text.split('\n')


def launch_prep(**kwargs):
    watch_paths = kwargs.get('watch_paths', None)
    if watch_paths is not None:
        print("Adding Missing Files")
        for path in watch_paths:
            DbMaintenence.add_all_files(path)
            DbMaintenence.fix_missing_pages()
            DbMaintenence.rebuild_missing_file_generated_content(
                rebuild=False,
                supress_error_ignore=False)
        print("Finished Adding Initial Files")
    print("Creating Missing Meta Files")
    DbMaintenence.gen_missing_meta_files()
    print("Finished Creating Missing Meta Files")


if __name__ == '__main__':
    try:
        parser = configparser.ConfigParser()
        with open('settings.ini', 'r') as settings_file:
            parser.read_file(settings_file)
            settings = configparser_as_dict(parser)
    except FileNotFoundError:
        settings = {}
    try:
        parser = configparser.ConfigParser()
        with open('config.ini', 'r') as config_file:
            parser.read_file(config_file)
            configs = configparser_as_dict(parser)
    except FileNotFoundError:
        configs = {}

    WebPages.initialize_module(settings=settings, config=configs)
    watcher = DbWatcher.create_database_watchman(config=configs)
    path_list = ini_str_to_list(settings.get('Watch', {}).get('paths', ''))
    for path in path_list:
        print(f"Watching ~ {path}")
        watcher.watch(path, True)

    Vap.initialize_module(settings=settings, config=configs)
    rest.initialize_module(settings=settings, config=configs)

    Vap.add_routes()
    # api.add_routes()
    rest.add_routes()
    WebPages.add_routes()

    launch_prep(watch_paths=path_list)
    watcher.observer.start()
    start_with_args()
    watcher.observer.join()
