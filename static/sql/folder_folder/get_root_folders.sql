select parent_id from folder_folder where parent_id not in (select DISTINCT child_id from folder_folder);
