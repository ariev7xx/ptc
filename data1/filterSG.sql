SELECT
    id,
    bucket_id,
    key_text,
    value_text
FROM records
WHERE json_valid(value_text)
  AND json_extract(value_text, '$.region') = 'SG';