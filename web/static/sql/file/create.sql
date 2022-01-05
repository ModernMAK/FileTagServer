CREATE TABLE IF NOT EXISTS file(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    mime TINYTEXT,
    name TINYTEXT,
    description TEXT,

    size_bytes INTEGER,
    hash_md5 BLOB,
    date_created INTEGER,
    date_modified INTEGER,
    date_uploaded INTEGER,
    date_updated INTEGER,
    CONSTRAINT path_unique UNIQUE (path)
);