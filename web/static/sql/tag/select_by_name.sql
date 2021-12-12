SELECT tag.id, tag.name, tag.description, COUNT(file_tag.file_id) AS count FROM tag
LEFT JOIN file_tag ON tag.id = file_tag.tag_id
WHERE tag.name = ?
GROUP BY tag.id;