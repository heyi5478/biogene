-- Runs once on first `db` container init (postgres image executes every
-- *.sql under /docker-entrypoint-initdb.d/ as POSTGRES_USER on POSTGRES_DB).
--
-- compose has already created role `gimc` and database `gimc` via the
-- POSTGRES_USER / POSTGRES_DB env vars, so this script only adds the
-- bits setup-postgres.sh contributes on a host install: extension +
-- five schemas. Re-running is a no-op (CREATE … IF NOT EXISTS).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS main     AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS external AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS nbs      AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS links    AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS ref      AUTHORIZATION gimc;

GRANT ALL ON SCHEMA public TO gimc;
