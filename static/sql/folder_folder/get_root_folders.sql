select * from folder WHERE folder.id not in (SELECT DISTINCT child_id from folder_folder)