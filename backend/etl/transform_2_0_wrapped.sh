#!/usr/bin/env bash
# Wraps transform_2_0.sql with varchar-widen + narrow-with-truncate so
# overlong source values don't break the INSERT.
#
# 2.0 source has many text fields where actual data exceeds the canonical
# varchar(N) limit (e.g. main.aa.result is varchar(64) but stg_main."aa"."AA-Result"
# has values up to 314 chars). transform_2_0.sql's COALESCE doesn't truncate,
# so INSERT fails on every long row. Editing transform_2_0.sql is fragile
# (it's auto-generated from column_mapping_2_0.yaml). This wrapper sidesteps
# that by:
#
#   1. Recording current varchar lengths into a TEMP table.
#   2. ALTER each varchar column → text (metadata-only, fast).
#   3. Run transform_2_0.sql body (TRUNCATE + INSERT, no length check).
#   4. ALTER each column back → varchar(N) USING LEFT(col, N) (truncates
#      overflows to fit; column rewrite, but small DBs).
#
# Everything is in one transaction. If transform fails, rollback restores
# both data and schema. The widen-narrow is invisible to alembic
# (alembic_version is untouched; final schema matches expected).
#
# Usage:
#   bash backend/etl/transform_2_0_wrapped.sh

set -euo pipefail

ETL_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_SQL="$ETL_DIR/transform_2_0.sql"
WRAPPED_SQL="/tmp/transform_2_0_wrapped.$$.sql"

trap 'rm -f "$WRAPPED_SQL"' EXIT

{
    cat <<'WRAP_HEAD'
BEGIN;

-- 1. Snapshot current varchar limits in main/external/nbs.
CREATE TEMP TABLE _varchar_backup ON COMMIT DROP AS
SELECT n.nspname AS schema_name,
       c.relname AS tbl,
       a.attname AS col,
       atttypmod - 4 AS len
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_type t ON a.atttypid = t.oid
WHERE n.nspname IN ('main', 'external', 'nbs')
  AND c.relkind = 'r'        -- ordinary tables only (skip indexes, seqs, views)
  AND t.typname = 'varchar'
  AND a.attnum > 0
  AND NOT a.attisdropped
  AND atttypmod > 0;

-- 2. Widen every varchar to text (metadata-only in PG; fast).
DO $widen$
DECLARE r record;
BEGIN
    FOR r IN SELECT schema_name, tbl, col FROM _varchar_backup LOOP
        EXECUTE format('ALTER TABLE %I.%I ALTER COLUMN %I TYPE text',
                       r.schema_name, r.tbl, r.col);
    END LOOP;
END $widen$;

-- 3. transform_2_0.sql body (BEGIN/COMMIT stripped — wrapped in this txn).
WRAP_HEAD

    # Strip the file's own BEGIN/COMMIT so it nests cleanly.
    sed -e '/^BEGIN;$/d' -e '/^COMMIT;$/d' "$SOURCE_SQL"

    cat <<'WRAP_TAIL'

-- 4. Narrow back to original varchar(N), truncating any overflowing values.
DO $narrow$
DECLARE r record;
BEGIN
    FOR r IN SELECT schema_name, tbl, col, len FROM _varchar_backup LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ALTER COLUMN %I TYPE varchar(%s) USING LEFT(%I, %s)',
            r.schema_name, r.tbl, r.col, r.len, r.col, r.len
        );
    END LOOP;
END $narrow$;

COMMIT;
WRAP_TAIL
} > "$WRAPPED_SQL"

echo "Running wrapped transform from $WRAPPED_SQL"
PGPASSWORD="${PGPASSWORD:-gimc}" psql \
    -h "${PGHOST:-127.0.0.1}" \
    -U "${PGUSER:-gimc}" \
    -d "${PGDATABASE:-gimc}" \
    -v ON_ERROR_STOP=1 \
    -f "$WRAPPED_SQL"
