CREATE TABLE IF NOT EXISTS file(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    mime TINYTEXT,
    name TINYTEXT,
    description TEXT,
    CONSTRAINT path_unique UNIQUE (path)
);