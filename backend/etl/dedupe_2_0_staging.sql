-- Pre-transform dedupe of patient-source staging tables.
--
-- transform_2_0.sql does `INSERT INTO <schema>.patient ... ON CONFLICT
-- (patient_id) DO UPDATE` from each source table, computing patient_id
-- as uuid_generate_v5 of the source key. PostgreSQL refuses an
-- INSERT...ON CONFLICT statement that contains two source rows mapping
-- to the same conflict key, with:
--
--   ON CONFLICT DO UPDATE command cannot affect row a second time
--
-- Source 2.0 data has many duplicates per key — including sentinels
-- like chartno='NA' (2190 rows in `2.0/基本資料`) plus genuine repeats
-- (same chartno appearing dozens of times). We delete duplicates here
-- so each (table, key) tuple has exactly one row before transform runs.
-- Tie-break: keep the row with the smallest physical position (ctid),
-- which is roughly insertion order from the source dump and is at least
-- deterministic per rerun.
--
-- Sentinel-chartno patients (one survivor per sentinel value) still get
-- inserted into canonical `patient` and become "buckets" for any sample
-- rows that referenced them. This is a known data-quality artifact at
-- the source and is left for downstream cleanup; only the duplicate
-- INSERT failure is fixed here.
--
-- Patient-source tables and their keys (from transform_2_0.sql):
--
--   stg_main."基本資料"      chartno
--   stg_main."opd"           "病歷號"
--   stg_external."基本資料"  chartno
--   stg_nbs."nbs"            "Screen_id"
--   stg_nbs."系統外自費"     "Screen_id"
--   stg_nbs."門診個案"       "Screen_id"

\echo 'dedupe stg_main."基本資料" by chartno'
DELETE FROM stg_main."基本資料" t
WHERE EXISTS (
    SELECT 1 FROM stg_main."基本資料" t2
    WHERE t2."chartno" = t."chartno"
      AND t2.ctid < t.ctid
);

\echo 'dedupe stg_main."opd" by 病歷號'
DELETE FROM stg_main."opd" t
WHERE EXISTS (
    SELECT 1 FROM stg_main."opd" t2
    WHERE t2."病歷號" = t."病歷號"
      AND t2.ctid < t.ctid
);

\echo 'dedupe stg_external."基本資料" by chartno'
DELETE FROM stg_external."基本資料" t
WHERE EXISTS (
    SELECT 1 FROM stg_external."基本資料" t2
    WHERE t2."chartno" = t."chartno"
      AND t2.ctid < t.ctid
);

\echo 'dedupe stg_nbs."nbs" by Screen_id'
DELETE FROM stg_nbs."nbs" t
WHERE EXISTS (
    SELECT 1 FROM stg_nbs."nbs" t2
    WHERE t2."Screen_id" = t."Screen_id"
      AND t2.ctid < t.ctid
);

\echo 'dedupe stg_nbs."系統外自費" by Screen_id'
DELETE FROM stg_nbs."系統外自費" t
WHERE EXISTS (
    SELECT 1 FROM stg_nbs."系統外自費" t2
    WHERE t2."Screen_id" = t."Screen_id"
      AND t2.ctid < t.ctid
);

\echo 'dedupe stg_nbs."門診個案" by Screen_id'
DELETE FROM stg_nbs."門診個案" t
WHERE EXISTS (
    SELECT 1 FROM stg_nbs."門診個案" t2
    WHERE t2."Screen_id" = t."Screen_id"
      AND t2.ctid < t.ctid
);

\echo 'dedupe complete'
