select = """SELECT file.id, file.path, file.mime, file.name, file.description, GROUP_CONCAT(DISTINCT file_tag.tag_id) as tags, folder_file.folder_id as parent_folder_id FROM file
LEFT JOIN file_tag on file_tag.file_id = file.id
LEFT JOIN folder_file on folder_file.file_id = file.id
GROUP BY file.id"""

create = """CREATE TABLE IF NOT EXISTS file(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    mime TINYTEXT,
    name TINYTEXT,
    description TEXT,
    CONSTRAINT path_unique UNIQUE (path)
)"""

select_by_ids = f"""SELECT * FROM ({select}) WHERE id in ({{file_ids}})"""
select_by_id = f"""SELECT * FROM ({select}) WHERE id = ?"""

select_orphaned_files = f"""SELECT * FROM ({select}) WHERE id not in in (select DISTINCT folder_file.file_id from folder_file)"""