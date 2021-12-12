SELECT file.id, path, mime, name, description, GROUP_CONCAT(file_tag.tag_id) as tags FROM file
LEFT JOIN file_tag on file_tag.file_id = file.id
WHERE file.id = ?
GROUP BY file.id;