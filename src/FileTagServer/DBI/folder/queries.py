select = """SELECT folder.id, folder.path, folder.name, folder.description, GROUP_CONCAT(DISTINCT folder_tag.tag_id) as tags, GROUP_CONCAT(DISTINCT folder_folder.child_id) as subfolders, GROUP_CONCAT(DISTINCT folder_file.file_id) as files FROM folder
LEFT JOIN folder_tag on folder_tag.folder_id = folder.id
LEFT JOIN folder_folder on folder_folder.parent_id = folder.id
LEFT JOIN folder_file on folder_file.folder_id = folder.id
GROUP BY folder.id"""

select_by_ids = f"""SELECT * FROM ({select}) WHERE id in ({{tag_ids}})"""
select_by_id = f"""SELECT * FROM ({select}) WHERE id =? """

select_root_folders = f"""SELECT * FROM ({select}) WHERE id not in (select DISTINCT child_id from folder_folder)"""


select_by_path = f"""SELECT * FROM ({select}) WHERE path = ?"""
