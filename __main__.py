from litespeed import start_with_args
import src.routing.virtual_access_points as Vap
import src.routing.rest as rest
import src.routing.web_pages as WebPages
# import src.dbmaintanence as DbMaintenence
# from src.content import content_gen_startup
# import src.file_watching.db_watcher as DbWatcher
from src.content.gen.content_gen_setup import initialize_gen

from src.database.main import create_all_tables, insert_files
from src.util import dict_util
from src.util.dict_util import DictFormat
import globals


# def launch_prep(**kwargs):
#     watch_paths = kwargs.get('watch_paths', None)
#     if watch_paths is not None:
#         print("Adding Missing Files")
#         for path in watch_paths:
#             DbMaintenence.add_all_files(path)
#             DbMaintenence.fix_missing_pages()
#             DbMaintenence.rebuild_missing_file_generated_content(supress_error_ignore=False)
#         print("Finished Adding Initial Files")
#     print("Creating Missing Meta Files")
#     DbMaintenence.gen_missing_meta_files()
#     print("Finished Creating Missing Meta Files")

def get_all_files(path: str):
    import os
    paths = []
    for root, _, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            paths.append(full_path)
    return paths


if __name__ == '__main__':
    try:
        settings = dict_util.read_dict('settings.ini', DictFormat.ini)
    except FileNotFoundError:
        settings = {}
    try:
        configs = dict_util.read_dict('config.ini', DictFormat.ini)
    except FileNotFoundError:
        configs = {}

    # content_gen_startup.initialize_content_gen()

    WebPages.initialize_module(settings=settings, config=configs)
    # watcher = DbWatcher.create_database_watchman(config=configs)
    path_list = settings.get('Watch', {}).get('paths', '').split('\n')

    db_path = configs.get('Launch Args', {}).get('db_path', {})
    create_all_tables(db_path=db_path)
    for path in path_list:
        insert_files(db_path, get_all_files(path))

    initialize_gen(globals.Viewable_Converter, globals.Thumbnail_Converter)

    # for path in path_list:
    #     print(f"Watching ~ {path}")
    #     watcher.watch(path, True)

    Vap.RequiredVap.add_to_vap()
    rest.initialize_module(settings=settings, config=configs)
    Vap.VirtualAccessPoints.add_routes()
    # api.add_routes()
    rest.add_routes()
    WebPages.add_routes()

    # launch_prep(watch_paths=path_list)
    # watcher.start(True)
    start_with_args()
    # watcher.observer.join()
