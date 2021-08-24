CREATE TABLE IF NOT EXISTS folder_folder (
    parent_id INTEGER,
    child_id INTEGER,
    CONSTRAINT pair_unique UNIQUE (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES folder (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (child_id) REFERENCES folder (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);