CREATE TABLE IF NOT EXISTS file_tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    tag_id INTEGER,
    CONSTRAINT pair_unique UNIQUE (file_id, tag_id),
    FOREIGN KEY (file_id) REFERENCES file (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (tag_id) REFERENCES tag (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);