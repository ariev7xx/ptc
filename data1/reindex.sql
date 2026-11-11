
CREATE TEMP TABLE bucket_map AS
SELECT id AS old_id,
       ROW_NUMBER() OVER (ORDER BY id) AS new_id
FROM buckets;

CREATE TABLE buckets_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    name TEXT NOT NULL
);

INSERT INTO buckets_new (id, parent_id, name)
SELECT m.new_id, p.new_id, b.name
FROM buckets b
JOIN bucket_map m ON b.id = m.old_id
LEFT JOIN bucket_map p ON b.parent_id = p.old_id
ORDER BY m.new_id;

CREATE TABLE records_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_id INTEGER NOT NULL,
    key_hex TEXT NOT NULL,
    key_text TEXT,
    value_text TEXT,
    value_blob BLOB,
    value_type TEXT NOT NULL
);

INSERT INTO records_new (
    id, bucket_id, key_hex, key_text,
    value_text, value_blob, value_type
)
SELECT
    ROW_NUMBER() OVER (ORDER BY r.id),
    m.new_id,
    r.key_hex,
    r.key_text,
    r.value_text,
    r.value_blob,
    r.value_type
FROM records r
JOIN bucket_map m ON r.bucket_id = m.old_id
ORDER BY r.id;

DROP TABLE records;
DROP TABLE buckets;

ALTER TABLE buckets_new RENAME TO buckets;
ALTER TABLE records_new RENAME TO records;

DELETE FROM sqlite_sequence
WHERE name IN ('buckets', 'records');

INSERT INTO sqlite_sequence(name, seq)
SELECT 'buckets', COALESCE(MAX(id), 0) FROM buckets;

INSERT INTO sqlite_sequence(name, seq)
SELECT 'records', COALESCE(MAX(id), 0) FROM records;

DROP TABLE bucket_map;
