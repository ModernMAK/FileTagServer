SELECT file.id, path, mime, name, description, GROUP_CONCAT(file_tag.tag_id) as tags FROM file
LEFT JOIN file_tag on file_tag.file_id = file.id
LEFT JOIN file_meta on file_meta.file_id = file.id
GROUP BY file.id;