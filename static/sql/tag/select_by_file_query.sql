SELECT id, name, description, count FROM (SELECT tag.id, tag.name, tag.description, COUNT(file_tag.file_id) AS count FROM tag
LEFT JOIN file_tag ON tag.id = file_tag.tag_id
GROUP BY tag.id)
inner JOIN file_tag ON id = file_tag.tag_id
where file_tag.file_id IN (<file_query>)
GROUP BY id;