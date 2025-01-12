CREATE DATABASE IF NOT EXISTS default;

CREATE TABLE IF NOT EXISTS default.reviews (
    id UInt64,
    title String,
    text String,
    grade UInt8,
    company_name String,
    region String,
    category String,
    date_create String,
    created_at String DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY id;
