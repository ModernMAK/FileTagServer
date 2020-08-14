# import os
# from typing import Union, Tuple, List
# from watchdog.events import DirMovedEvent, FileMovedEvent, \
#     DirCreatedEvent, FileCreatedEvent, \
#     DirDeletedEvent, FileDeletedEvent, \
#     DirModifiedEvent, FileModifiedEvent
#
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
#
#
# class Watchman:
#     def __init__(self, **kwargs):
#         self.observer = kwargs.get('observer', Observer())
#         self.watchlist = []
#         self.default_handler = kwargs.get('default_handler', WatchmanHandler())
#
#     def start(self, run_watch_on_startup=False):
#         self.observer.start()
#         if run_watch_on_startup:
#             for watch in self.watchlist:
#                 handlers = self.observer._handlers[watch]
#                 if watch.is_recursive:
#                     for root, directories, files in os.walk(watch.path):
#                         for file in files:
#                             full_file = os.path.join(root, file)
#                             for handler in handlers:
#                                 handler.on_created(FileCreatedEvent(src_path=full_file))
#                         for dir in directories:
#                             full_dir = os.path.join(root, dir)
#                             for handler in handlers:
#                                 handler.on_created(DirCreatedEvent(src_path=full_dir))
#                 else:
#                     for handler in handlers:
#                         full_file = watch.path
#                         if os.path.isdir(full_file):
#                             handler.on_created(DirCreatedEvent(src_path=full_file))
#                         else:
#                             handler.on_created(FileCreatedEvent(src_path=full_file))
#
#     def stop(self):
#         self.observer.stop()
#
#     def watch(self, path: str, recursive: bool = False, handler: FileSystemEventHandler = None):
#         if handler is None:
#             handler = self.default_handler
#         watch = self.observer.schedule(handler, path, recursive)
#         self.watchlist.append(watch)
#
#     def watch_many(self, paths: List[Union[str, Tuple[str, bool]]], handler: FileSystemEventHandler = None):
#         if handler is None:
#             handler = self.default_handler
#         for path_info in paths:
#             path_recursive = False
#             if isinstance(path_info, tuple):
#                 path_str, path_recursive = path_info
#             else:
#                 path_str = path_info
#             self.watch(path_str, path_recursive, handler)
#
#     # Ill come up with a better way of doing this later
#     def unwatch(self, path: str, recursive: bool = False):
#         for watch in self.watchlist:
#             if watch.path == path and watch.is_recursive == recursive:
#                 self.observer.unschedule(watch)
#                 return True
#         return False
#
#     # Ill come up with a better way of doing this later
#     def unwatch_many(self, paths: List[Union[str, Tuple[str, bool]]]):
#         results = []
#         for path_info in paths:
#             if isinstance(path_info, tuple):
#                 path_str, path_recursive = path_info
#             else:
#                 path_str, path_recursive = path_info, False
#             results.append(self.unwatch(path_str, path_recursive))
#         return results
#
#     def unwatch_all(self):
#         self.observer.unschedule_all()
#         self.watchlist.clear()
#         return True
#
#     # Data-Design wise it seems Dir*Event and File*Event are identical,
#     # but i might need to do different logic for directories than files,
#     # so i do a check in  each function
#
#
# class WatchmanHandler(FileSystemEventHandler):
#     def __init__(self, **kwargs):
#         self.log_events = kwargs.get('log_events', False)
#
#     def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
#         # Directory moved
#         if isinstance(event, DirMovedEvent):
#             self.on_dir_renamed(event)
#         # File moved
#         else:
#             self.on_file_renamed(event)
#
#     def on_file_renamed(self, event: FileMovedEvent):
#         if self.log_events:
#             print(f"F_Renamed: {event.src_path} -> {event.dest_path}")
#         pass
#
#     def on_dir_renamed(self, event: DirMovedEvent):
#         if self.log_events:
#             print(f"D_Renamed: {event.src_path} -> {event.dest_path}")
#         pass
#
#     def on_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]):
#         # Directory moved
#         if isinstance(event, DirCreatedEvent):
#             self.on_dir_found(event)
#         # File moved
#         else:
#             self.on_file_found(event)
#
#     def on_file_found(self, event: FileCreatedEvent):
#         if self.log_events:
#             print(f"F_Found: {event.src_path}")
#         pass
#
#     def on_dir_found(self, event: DirCreatedEvent):
#         if self.log_events:
#             print(f"D_Found: {event.src_path}")
#         pass
#
#     def on_deleted(self, event: Union[DirDeletedEvent, FileDeletedEvent]):
#         # Directory moved
#         if isinstance(event, DirDeletedEvent):
#             self.on_dir_lost(event)
#         # File moved
#         else:
#             self.on_file_lost(event)
#
#     def on_file_lost(self, event: FileDeletedEvent):
#         if self.log_events:
#             print(f"F_LOST: {event.src_path}")
#         pass
#
#     def on_dir_lost(self, event: DirDeletedEvent):
#         if self.log_events:
#             print(f"D_Lost: {event.src_path}")
#         pass
#
#     def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]):
#         # Directory moved
#         if isinstance(event, DirModifiedEvent):
#             self.on_dir_changed(event)
#         # File moved
#         else:
#             self.on_file_changed(event)
#
#     def on_file_changed(self, event: FileModifiedEvent):
#         if self.log_events:
#             print(f"F_Changed: {event.src_path}")
#         pass
#
#     def on_dir_changed(self, event: DirModifiedEvent):
#         if self.log_events:
#             print(f"D_Changed: {event.src_path}")
#         pass
