from src.database_api.clients.file import FileClient
from src.database_api.clients.file_extra_info import FileExtraInfoClient
from src.database_api.clients.file_tag_map import FileTagMapClient
from src.database_api.clients.tag import TagClient
from src.database_api.util import BaseClient


class MasterClient(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        db_path = kwargs.get('db_path')
        self.file_info = FileExtraInfoClient(db_path=db_path)
        self.file = FileClient(db_path=db_path)
        self.tag = TagClient(db_path=db_path)
        self.map = FileTagMapClient(db_path=db_path)

    def create_all(self):
        self.file.create()
        self.tag.create()
        self.map.create()
        self.file_info.create()
