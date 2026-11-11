SELECT 'buckets' AS tabel, COUNT(*) AS jumlah,
       MIN(id) AS id_min, MAX(id) AS id_max
FROM buckets
UNION ALL
SELECT 'records', COUNT(*), MIN(id), MAX(id)
FROM records;