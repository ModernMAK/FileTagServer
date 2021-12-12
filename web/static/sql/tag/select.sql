SELECT tag.id, tag.name, tag.description, file_count + folder_count as count FROM tag
LEFT JOIN (SELECT COUNT(tag.id) as file_count from tag left join file_tag on tag.id = file_tag.tag_id GROUP by tag.id) ON tag.id = tag.id
LEFT JOIN (SELECT COUNT(tag.id) as folder_count from tag left join folder_tag on tag.id = folder_tag.tag_id GROUP by tag.id) ON tag.id = tag.id;