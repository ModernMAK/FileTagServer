select file.id from file where file.id not in (select DISTINCT folder_file.file_id from folder_file);
