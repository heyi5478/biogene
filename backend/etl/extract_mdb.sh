#!/usr/bin/env bash
# extract_mdb.sh — dump every table in gene.mdb to one CSV per table.
#
# Usage:
#   bash backend/etl/extract_mdb.sh /path/to/gene.mdb /path/to/out_dir
#
# Output:
#   <out_dir>/<TABLE>.csv          for every table mdb-tables reports
#
# BLOB-bearing tables (MSDATA, GCDATA, MPSUDATA, ENZYME) are also dumped
# here (sans the BLOB bytes — mdb-export emits them as nulls). Use
# extract_blobs_mdb.py to materialise the BLOB content separately.
#
# We need mdbtools >= 0.7 for `--no-quote` to behave well with Chinese
# columns; older versions sometimes mis-quote utf-8 strings.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <path-to-gene.mdb> <out-dir>" >&2
  exit 64
fi

MDB="$1"
OUT="$2"

if ! command -v mdb-tables >/dev/null; then
  echo "mdb-tools not on PATH (apt install mdbtools)" >&2
  exit 127
fi
if [[ ! -f "$MDB" ]]; then
  echo "mdb file not found: $MDB" >&2
  exit 66
fi

mkdir -p "$OUT"

# `mdb-tables -1` prints one table name per line. Strip carriage returns
# in case the .mdb came from Windows.
tables=$(mdb-tables -1 "$MDB" | tr -d '\r' | sed '/^[[:space:]]*$/d')

echo "extract_mdb.sh: $(echo "$tables" | wc -l) tables → $OUT"
for t in $tables; do
  case "$t" in
    # Tables explicitly excluded by the legacy-data-etl spec.
    users|operator|doctor|CELLDATA|opd_tmp|disease_count|G0001|G0016|G0017)
      echo "  skip   $t  (exclusion list)"
      continue
      ;;
  esac
  echo "  export $t"
  mdb-export -D '%Y-%m-%d %H:%M:%S' "$MDB" "$t" > "$OUT/$t.csv"
done

echo "extract_mdb.sh: done"
