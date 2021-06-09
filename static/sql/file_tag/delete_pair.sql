DELETE FROM file_tag
WHERE file_tag.file_id = :file_id
  AND file_tag.tag_id = :tag_id;