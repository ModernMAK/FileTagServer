CREATE TABLE IF NOT EXISTS folder(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    name TINYTEXT,
    description TEXT,
    CONSTRAINT path_unique UNIQUE (path)
);