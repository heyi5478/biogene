-- post_pgloader.sql — run AFTER pgloader_2_0.load against EACH target schema.
--
-- pgloader can't always pick the right PG type for legacy MySQL columns;
-- partial indexes, triggers, and `ntubiogene_sampleno` aren't expressible
-- in the pgloader CAST grammar. We patch those up here.
--
-- Usage: `psql -v target=<schema> -f post_pgloader.sql -d gimc`
--   $target ∈ { main, external, nbs }
--
-- Idempotent — every DDL is wrapped in IF NOT EXISTS / DO blocks. Safe
-- to re-run after a partial pgloader failure.

\set ON_ERROR_STOP on
\set target_schema :target

\echo '=== post-pgloader patches for schema:' :target_schema ' ==='

-- 1. patient_id: pgloader brings it in as VARCHAR(36); we store native UUID.
DO $do$
DECLARE
    tbl text;
BEGIN
    -- main.patient.patient_id is the PK; sample tables have it as FK.
    -- We cast both directions in one sweep.
    FOR tbl IN
        SELECT c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = :'target_schema'
          AND c.column_name = 'patient_id'
          AND c.data_type IN ('character varying', 'text', 'character')
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ALTER COLUMN patient_id TYPE UUID USING patient_id::uuid',
            :'target_schema', tbl
        );
    END LOOP;
END
$do$;

-- 2. ntubiogene_sampleno + v2_source_schema — ETL provenance columns.
--    Always present in the 3.0 model but not in 2.0 source data.
DO $do$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT c.table_name
        FROM information_schema.tables c
        WHERE c.table_schema = :'target_schema'
          AND c.table_name <> 'patient'
          AND c.table_type = 'BASE TABLE'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I '
            '  ADD COLUMN IF NOT EXISTS ntubiogene_sampleno VARCHAR(64), '
            '  ADD COLUMN IF NOT EXISTS v2_source_schema    VARCHAR(32) '
            '    DEFAULT %L',
            :'target_schema', tbl, :'target_schema'
        );
    END LOOP;
END
$do$;

-- 3. created_at / updated_at — pgloader will skip if not in source. Add.
DO $do$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT c.table_name
        FROM information_schema.tables c
        WHERE c.table_schema = :'target_schema'
          AND c.table_type = 'BASE TABLE'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I '
            '  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(), '
            '  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()',
            :'target_schema', tbl
        );
    END LOOP;
END
$do$;

-- 4. BEFORE UPDATE trigger calling public.set_updated_at() on every table
--    that has both timestamp columns. The function itself is created by
--    the alembic baseline.
DO $do$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = :'target_schema'
          AND c.column_name = 'updated_at'
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%I_set_updated_at ON %I.%I',
            tbl, :'target_schema', tbl
        );
        EXECUTE format(
            'CREATE TRIGGER trg_%I_set_updated_at '
            '  BEFORE UPDATE ON %I.%I '
            '  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()',
            tbl, :'target_schema', tbl
        );
    END LOOP;
END
$do$;

-- 5. Partial indexes on hot WHERE-clauses (mirrors the alembic baseline
--    so the verify.py performance check passes regardless of which path
--    populated the data).
DO $do$
DECLARE
    has_aa_leu        boolean;
    has_bm_lyso       boolean;
    has_cah_ohp17     boolean;
    has_dmd_tsh_tsh   boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = :'target_schema' AND table_name = 'aa' AND column_name = 'leu'
    ) INTO has_aa_leu;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = :'target_schema' AND table_name = 'biomarker' AND column_name = 'dbs_lyso_gb3'
    ) INTO has_bm_lyso;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = :'target_schema' AND table_name = 'cah' AND column_name = 'ohp17'
    ) INTO has_cah_ohp17;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = :'target_schema' AND table_name = 'dmd_tsh' AND column_name = 'tsh'
    ) INTO has_dmd_tsh_tsh;

    IF has_aa_leu THEN
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS ix_aa_leu_notnull ON %I.aa (leu) WHERE leu IS NOT NULL',
            :'target_schema'
        );
    END IF;
    IF has_bm_lyso THEN
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS ix_biomarker_lyso_high ON %I.biomarker (dbs_lyso_gb3) WHERE dbs_lyso_gb3 > 5',
            :'target_schema'
        );
    END IF;
    IF has_cah_ohp17 THEN
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS ix_cah_ohp17_notnull ON %I.cah (ohp17) WHERE ohp17 IS NOT NULL',
            :'target_schema'
        );
    END IF;
    IF has_dmd_tsh_tsh THEN
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS ix_dmd_tsh_tsh_notnull ON %I.dmd_tsh (tsh) WHERE tsh IS NOT NULL',
            :'target_schema'
        );
    END IF;
END
$do$;

\echo 'post_pgloader.sql complete for' :target_schema
