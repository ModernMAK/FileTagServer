from FileTagServer.DBI.common import AbstractDBI
from FileTagServer.DBI.file.file import FileDBI
from FileTagServer.DBI.folder.folder import FolderDBI
from FileTagServer.DBI.tag.tag import TagDBI


class Database(AbstractDBI):
    def __init__(self, db_filepath):
        super().__init__(db_filepath)
        self.file = FileDBI(db_filepath)
        self.folder = FolderDBI(db_filepath)
        self.tag = TagDBI(db_filepath)