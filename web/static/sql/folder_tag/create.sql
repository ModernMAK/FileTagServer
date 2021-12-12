CREATE TABLE IF NOT EXISTS folder_tag (
    folder_id INTEGER,
    tag_id INTEGER,
    CONSTRAINT pair_unique UNIQUE (folder_id, tag_id),
    FOREIGN KEY (folder_id) REFERENCES folder (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (tag_id) REFERENCES tag (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);