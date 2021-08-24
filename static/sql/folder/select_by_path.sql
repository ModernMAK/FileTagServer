SELECT folder.id, path, name, description, GROUP_CONCAT(folder_tag.tag_id) as tags FROM folder
LEFT JOIN folder_tag on folder_tag.folder_id = folder.id
WHERE folder.path = ?
GROUP BY folder.id;