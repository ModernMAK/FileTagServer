CREATE TABLE IF NOT EXISTS folder_file (
    folder_id INTEGER,
    file_id INTEGER,
    CONSTRAINT pair_unique UNIQUE (folder_id, file_idinsert.sql),
    FOREIGN KEY (folder_id) REFERENCES folder (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (file_id) REFERENCES file (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);