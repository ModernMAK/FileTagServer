from litespeed import start_with_args, App
from src.database_api.clients import MasterClient
import src.config as config
from src.page_groups import FilePageGroup, StatusPageGroup, StaticGroup, TagPageGroup, UploadGroup

if __name__ == '__main__':
    client = MasterClient(db_path=config.db_path).create_all()
    groups = [
        StatusPageGroup,
        FilePageGroup,
        TagPageGroup,
        StaticGroup,
        UploadGroup
    ]

    for group in groups:
        group.add_routes()
        group.initialize()

    print("\n".join(App._urls))

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
