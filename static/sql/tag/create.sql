CREATE TABLE IF NOT EXISTS tag(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TINYTEXT,
    description TEXT,
    CONSTRAINT name_unique UNIQUE (name)
);