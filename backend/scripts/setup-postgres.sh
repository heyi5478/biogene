#!/usr/bin/env bash
# Provision a PostgreSQL 16 instance for the my-project DEV environment.
#
# Idempotent: running twice is safe — apt install skips, role/db/schemas use
# IF NOT EXISTS / DO NOTHING patterns.
#
# Usage:
#   sudo bash backend/scripts/setup-postgres.sh
#
# After this script:
#   - PostgreSQL 16 listens on localhost:5432
#   - role gimc / password gimc / database gimc exist
#   - schemas main, external, nbs, links, ref are created
#   - uuid-ossp extension is installed
#   - DATABASE_URL=postgresql+asyncpg://gimc:gimc@localhost:5432/gimc works

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: must run as root (use sudo)" >&2
  exit 1
fi

. /etc/os-release
CODENAME="${VERSION_CODENAME:-jammy}"

echo ">>> [1/5] Adding PostgreSQL APT repository (pgdg) for ${CODENAME}"
install -d -m 0755 /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/pgdg.gpg ]]; then
  curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | gpg --dearmor -o /etc/apt/keyrings/pgdg.gpg
fi
echo "deb [signed-by=/etc/apt/keyrings/pgdg.gpg] http://apt.postgresql.org/pub/repos/apt ${CODENAME}-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list

echo ">>> [2/5] apt update + install postgresql-16 + client + contrib"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    postgresql-16 postgresql-client-16 postgresql-contrib-16

echo ">>> [3/5] Ensuring postgresql is running"
if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running --quiet 2>/dev/null; then
  systemctl enable --now postgresql
else
  # Inside containers without systemd, fall back to pg_ctlcluster.
  pg_ctlcluster 16 main start || true
fi

echo ">>> [4/5] Creating role and database (idempotent)"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gimc') THEN
      CREATE ROLE gimc LOGIN PASSWORD 'gimc';
   END IF;
END
$$;

-- PG 16 ICU collation: LOCALE_PROVIDER + ICU_LOCALE; LC_COLLATE/LC_CTYPE
-- still must be a real glibc locale so we use C.UTF-8 (always available).
SELECT 'CREATE DATABASE gimc OWNER gimc ENCODING ''UTF8'' LOCALE_PROVIDER icu ICU_LOCALE ''und-x-icu'' LC_COLLATE ''C.UTF-8'' LC_CTYPE ''C.UTF-8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'gimc')\gexec
SQL

echo ">>> [5/5] Installing uuid-ossp + creating schemas main/external/nbs/links/ref"
sudo -u postgres psql -v ON_ERROR_STOP=1 -d gimc <<'SQL'
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS main    AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS external AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS nbs     AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS links   AUTHORIZATION gimc;
CREATE SCHEMA IF NOT EXISTS ref     AUTHORIZATION gimc;
GRANT ALL ON SCHEMA public TO gimc;
SQL

echo
echo "OK — PostgreSQL 16 ready."
echo "Verify with:  PGPASSWORD=gimc psql -h localhost -U gimc -d gimc -c '\\dn'"
