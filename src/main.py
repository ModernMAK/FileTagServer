from litespeed import start_with_args, App
from src.database_api.clients import MasterClient
import src.config as config
from src.page_groups.file_page_group import FilePageGroup
from src.page_groups import status
from src.page_groups.tag_page_group import TagPageGroup
from src.page_groups.static import Static

if __name__ == '__main__':
    client = MasterClient(db_path=config.db_path).create_all()
    status.add_routes()
    status.initialize_module()

    FilePageGroup.add_routes()
    FilePageGroup.initialize()

    TagPageGroup.add_routes()
    TagPageGroup.initialize()

    Static.add_routes()

    temp = [v for v in App._urls.keys()]
    print("\n".join(temp))

    start_with_args()

    # WebPages
    #
    # WebPages.initialize_module(settings=settings, config=configs)
    # watcher = DbWatcher.create_database_watchman(config=configs)
    # path_list = settings.get('Watch', {}).get('paths', '').split('\n')
    # for path in path_list:
    #     print(f"Watching ~ {path}")
    #     watcher.watch(path, True)
    #
    # Vap.RequiredVap.add_to_vap()
    # rest.initialize_module(settings=settings, config=configs)
    # Vap.VirtualAccessPoints.add_routes()
    # # database_api.add_routes()
    # rest.add_routes()
    # WebPages.add_routes()
    #
    # # launch_prep(watch_paths=path_list)
    # watcher.start(True)
    # start_with_args()
    # watcher.observer.join()
