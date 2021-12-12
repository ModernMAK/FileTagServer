from FileTagServer.DBI.common import AbstractDBI
from FileTagServer.DBI.file.file import FileDBI
from FileTagServer.DBI.folder.folder import FolderDBI
from FileTagServer.DBI.folder_children import FolderChildrenDBI
from FileTagServer.DBI.tag.tag import TagDBI


class Database(AbstractDBI):
    def __init__(self, db_filepath: str, sql_dirpath: str):
        super().__init__(db_filepath, sql_dirpath)
        self.file = FileDBI(db_filepath, sql_dirpath)
        self.folder = FolderDBI(db_filepath, sql_dirpath)
        self.tag = TagDBI(db_filepath, sql_dirpath)
        self.folder_children = FolderChildrenDBI(db_filepath,sql_dirpath)
